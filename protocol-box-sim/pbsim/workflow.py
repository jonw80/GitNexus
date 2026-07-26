"""pb-workflow: the orchestrator from section 14.3 (processor.js).

`WorkflowProcessor.process_document` is a faithful port of the switch statement
in the build file. The `hardened` profile layers on the controls this simulation
recommends; every one of them is gated behind `self.hardened` so the baseline
run reproduces v4.1 behaviour exactly.
"""

from .backends import ERPClient, FHIRClient
from .spec import CLASSIFICATION_MARKINGS
from .telephony import OutboundFaxJob


class WorkflowResult:
    def __init__(self, disposition, action, **extra):
        self.disposition = disposition
        self.action = action
        self.extra = extra

    def as_dict(self):
        return {"disposition": self.disposition, "action": self.action, **self.extra}


class WorkflowProcessor:
    def __init__(self, case, rng, audit, profile="baseline"):
        self.case = case
        self.rng = rng
        self.audit = audit
        self.profile = profile
        self.hardened = profile == "hardened"
        self.fhir = FHIRClient(audit)
        self.erp = ERPClient(audit)
        self.outbound = []
        self.controls_fired = []

    # -- hardened-only controls ---------------------------------------------

    def _check_spillage(self, text):
        """Proposed control PB-C1: classification banner detection.

        v4.1 has no equivalent. A SECRET-marked page arriving on an unclassified
        DID is currently OCR'd, classified, and potentially auto-replied to.
        """
        upper = text.upper()
        for marking in CLASSIFICATION_MARKINGS:
            if marking in upper:
                return marking
        return None

    def _reply_path(self, entities):
        """Resolve where a reply fax would go."""
        fax = entities.get("FAX_NUMBER")
        if fax and fax.get("value"):
            return fax["value"], "entity"
        if self.case.caller_id:
            return self.case.caller_id, "caller_id_fallback"
        return None, None

    def _entity_floor(self, entities, required):
        """Proposed control PB-C4: per-entity confidence floor.

        Section 12.3 gates on the document average only, so a 0.31-confidence
        part number rides through inside a 0.88-average document.
        """
        weak = []
        for etype in required:
            ent = entities.get(etype)
            if ent is None:
                weak.append((etype, "missing"))
            elif ent["confidence"] is not None and ent["confidence"] < 0.60:
                weak.append((etype, f"conf {ent['confidence']:.2f}"))
        return weak

    # -- dispatch ------------------------------------------------------------

    def process_document(self, doc):
        intent = doc["intent"]
        entities = doc["entities"]
        text = doc["text"]

        self.audit.log("PROCESS_START", intent=intent, source_fax=self.case.case_id)

        if self.hardened:
            marking = self._check_spillage(text)
            if marking:
                self.controls_fired.append("PB-C1 spillage guard")
                self.audit.log(
                    "SPILLAGE_QUARANTINE", marking=marking,
                    did=self.case.did, sku=self.case.sku,
                    auto_reply_suppressed=True, ocr_export_blocked=True,
                )
                return WorkflowResult(
                    "QUARANTINE", "Classification banner detected; document sealed, "
                    "no OCR export, no auto-reply, security officer notified",
                    marking=marking,
                )

        self.audit.log(
            "INTENT_CLASSIFIED", type=intent,
            confidence=doc["confidence"],
            entities={k: v["value"] for k, v in entities.items()},
        )

        # Section 14.3 switch, verbatim.
        if intent == "RECORDS_REQUEST":
            return self.handle_records_request(entities, doc)
        if intent == "PURCHASE_ORDER":
            return self.handle_purchase_order(entities, doc)
        if intent == "CLARIFICATION_NEEDED":
            return self.route_to_human_review(doc, reason=doc.get("review_rule", "low confidence"))
        if intent == "SPAM_OTHER":
            return self.archive_only(doc)

        if self.hardened:
            handler = {
                "LAB_RESULT": ("provider inbox", "Route to provider inbox"),
                "PRESCRIPTION_REFILL": ("pharmacy queue", "Route to pharmacy queue"),
                "INSURANCE_DENIAL": ("billing dept", "Route to billing dept"),
                "RFQ_QUOTE": ("sales/estimating queue", "Route to estimating; no ERP order created"),
                "ORDER_CHANGE": ("order desk", "Route to order desk for PO amendment"),
                "INVOICE_REMITTANCE": ("accounts payable", "Route to AP workflow"),
                "MRO_WORK_ORDER": ("CMMS intake", "Create or attach to CMMS work order"),
                "MILSTRIP_REQUISITION": ("DLA requisition queue", "Validate NSN and route to supply"),
                "CONTRACT_DOCUMENT": ("contracts inbox", "Route to contract administration"),
                "LEGAL_RECORDS_REQUEST": ("legal/HIM records officer",
                                          "Route to records custodian; EMR access not authorised"),
            }.get(intent)
            if handler:
                queue, action = handler
                self.controls_fired.append("PB-C2 extended taxonomy")
                self.audit.log("ROUTED", queue=queue, intent=intent)
                return WorkflowResult("ROUTE", action, queue=queue)

        # Section 14.3 `default:` — every intent class without an explicit case
        # lands here, including LAB_RESULT, PRESCRIPTION_REFILL and
        # INSURANCE_DENIAL, whose section 13.2 actions are never reachable.
        return self.route_to_human_review(
            doc, reason=f"no handler in processor.js switch for {intent}"
        )

    # -- handlers ------------------------------------------------------------

    def handle_records_request(self, entities, doc):
        if self.hardened:
            # Proposed control PB-C3: PHI scope guard. Only reach into the EMR
            # when the request carries clinical provenance.
            clinical_markers = ("mrn", "medical record", "hipaa", "treatment",
                                "discharge", "progress note", "physician", "clinic")
            has_mrn = "MRN" in entities
            clinical_did = self.case.did_class == "clinical"
            body = doc["text"].lower()
            marker_hits = sum(1 for m in clinical_markers if m in body)
            legal_request = any(
                t in body for t in ("subpoena", "law offices", "attorney",
                                    "employment record", "personnel file", "litigation")
            )
            if legal_request or not (has_mrn or clinical_did or marker_hits >= 2):
                self.controls_fired.append("PB-C3 PHI scope guard")
                self.audit.log(
                    "PHI_SCOPE_BLOCK",
                    reason="legal/non-clinical requester" if legal_request
                    else "insufficient clinical provenance",
                    fhir_query_suppressed=True,
                )
                return WorkflowResult(
                    "HUMAN_REVIEW",
                    "PHI scope guard blocked EMR query; routed to HIM/ROI officer "
                    "for authorization verification",
                    reason="non-clinical records request",
                )

        name = entities.get("PATIENT_NAME", {}).get("value")
        dob = entities.get("DATE_OF_BIRTH", {}).get("value")
        mrn = entities.get("MRN", {}).get("value")

        patient = self.fhir.find_patient(name=name, dob=dob, mrn=mrn)
        if not patient:
            self.audit.log("PROCESS_ERROR", reason="Patient not found")
            return self.create_error_response("Patient not found", doc)

        documents = self.fhir.get_documents(patient["id"], count=3)

        dest, dest_source = self._reply_path(entities)
        if self.hardened and dest_source == "caller_id_fallback":
            self.controls_fired.append("PB-C5 reply-path guard")
            self.audit.log("REPLY_PATH_BLOCK", reason="no verified fax-back number for PHI")
            return WorkflowResult(
                "HUMAN_REVIEW",
                "No verified fax-back number on a PHI payload; held for operator",
                reason="unverified reply path",
            )
        if dest is None:
            return self.route_to_human_review(doc, reason="no reply destination")

        send = self._send_fax(dest, pages=len(documents) + 1, label="records")
        self.audit.log(
            "RECORDS_SENT", patient=patient["id"],
            document_count=len(documents), destination=dest,
            status=send["status"],
        )
        return WorkflowResult(
            "AUTO_ACTION",
            f"Retrieved {len(documents)} documents for {patient['id']} and faxed to {dest}",
            documents_sent=len(documents), destination=dest, patient=patient["id"],
            fax=send, phi_released=True, reply_path=dest_source,
        )

    def handle_purchase_order(self, entities, doc):
        part = entities.get("PART_NUMBER", {}).get("value")
        qty_raw = entities.get("QUANTITY", {}).get("value")
        qty = None
        if qty_raw:
            digits = "".join(ch for ch in qty_raw if ch.isdigit())
            qty = int(digits) if digits else None

        if self.hardened:
            weak = self._entity_floor(entities, ["PART_NUMBER", "QUANTITY"])
            if weak:
                self.controls_fired.append("PB-C4 entity confidence floor")
                self.audit.log("ENTITY_FLOOR_BLOCK", weak=weak)
                return WorkflowResult(
                    "HUMAN_REVIEW",
                    "Order-critical entities below confidence floor: "
                    + ", ".join(f"{t} ({why})" for t, why in weak),
                    reason="weak order entities",
                )

        if not part or qty is None:
            self.audit.log("PROCESS_ERROR", reason="missing part number or quantity")
            return self.route_to_human_review(
                doc, reason=f"incomplete order (part={part!r}, qty={qty!r})"
            )

        inventory = self.erp.check_inventory(part)
        if not inventory["found"]:
            # v4.1 processor.js compares `inventory.available < entities.QUANTITY`
            # with available === undefined, which is false, so an unknown part
            # falls through into order creation.
            if self.hardened:
                self.controls_fired.append("PB-C6 unknown-part guard")
                return WorkflowResult(
                    "HUMAN_REVIEW", f"Part {part} not in ERP catalogue", reason="unknown part"
                )
            self.audit.log(
                "DEFECT_UNDEFINED_INVENTORY", part=part,
                note="available is undefined; `undefined < qty` is false, guard bypassed",
            )

        available = inventory["available"]
        if available is not None and available < qty:
            self.audit.log("INSUFFICIENT_INVENTORY", part=part, available=available, requested=qty)
            return self.route_to_human_review(
                doc, reason=f"INSUFFICIENT_INVENTORY: {available} available, {qty} requested"
            )

        order = self.erp.create_sales_order({
            "partNumber": part,
            "quantity": qty,
            "customerPO": entities.get("PO_NUMBER", {}).get("value"),
            "shipTo": entities.get("FACILITY_NAME", {}).get("value"),
        })
        ack = self.erp.get_order_acknowledgment(order["id"])

        dest, dest_source = self._reply_path(entities)
        if dest is None:
            return self.route_to_human_review(
                doc, reason="order created but no reply destination", order_id=order["id"]
            )

        send = self._send_fax(dest, pages=ack["pages"], label="order-ack")
        self.audit.log("ORDER_CREATED", order_id=order["id"], part=part, quantity=qty)
        return WorkflowResult(
            "AUTO_ACTION",
            f"Created {order['id']} for {qty} x {part}; acknowledgment faxed to {dest}",
            order_id=order["id"], part_number=part, quantity=qty,
            destination=dest, fax=send, reply_path=dest_source,
            part_found=inventory["found"],
        )

    def route_to_human_review(self, doc, reason, **extra):
        self.audit.log("HUMAN_REVIEW_QUEUED", reason=reason, intent=doc.get("intent"))
        return WorkflowResult("HUMAN_REVIEW", f"Queued for operator: {reason}",
                              reason=reason, **extra)

    def archive_only(self, doc):
        self.audit.log("ARCHIVED", intent=doc.get("intent"))
        return WorkflowResult("ARCHIVE", "Archived, no action taken")

    def create_error_response(self, message, doc):
        return WorkflowResult("HUMAN_REVIEW", f"Error response: {message}", reason=message)

    def _send_fax(self, destination, pages, label):
        job_id = f"FAX-{self.case.case_id}-{label}"
        job = OutboundFaxJob(
            job_id, destination, pages, self.rng, self.audit,
            line_quality=min(0.97, self.case.line_quality + 0.10),
        )
        result = job.send()
        self.outbound.append({"job_id": job_id, **result})
        return result
