"""Mock systems of record: FHIR R4 EMR (14.1.1) and REST ERP (14.2.1).

Deterministic stand-ins so the workflow engine exercises the same success,
not-found and insufficient-inventory branches the real drivers would hit.
"""


class FHIRClient:
    """Section 14.1.1 FHIR R4 client."""

    PATIENTS = {
        ("john smith", "01/15/1980"): {"id": "Patient/40021", "mrn": "12345678"},
        ("maria delgado", "07/22/1966"): {"id": "Patient/40088", "mrn": "22910044"},
    }

    def __init__(self, audit):
        self.audit = audit
        self.calls = []

    def find_patient(self, name=None, dob=None, mrn=None):
        self.calls.append({"op": "Patient?search", "name": name, "dob": dob, "mrn": mrn})
        key = ((name or "").strip().lower(), (dob or "").strip())
        patient = self.PATIENTS.get(key)
        if not patient and mrn:
            for p in self.PATIENTS.values():
                if p["mrn"] == mrn:
                    patient = p
                    break
        self.audit.log(
            "FHIR_PATIENT_SEARCH",
            query_name=name, query_dob=dob, query_mrn=mrn,
            result=patient["id"] if patient else "no match",
            http_status=200,
        )
        return patient

    def get_documents(self, patient_id, doc_type=None, count=3):
        self.calls.append({"op": "DocumentReference?patient", "patient": patient_id})
        docs = [f"DocumentReference/{patient_id.split('/')[-1]}-{i}" for i in range(1, count + 1)]
        self.audit.log("FHIR_DOCS_RETRIEVED", patient=patient_id, count=len(docs), http_status=200)
        return docs


class ERPClient:
    """Section 14.2.1 generic REST ERP client (SAP S/4HANA, Oracle, Plex)."""

    INVENTORY = {
        "BRG-6205-2RS": 480,
        "HYD-SEAL-K4471": 26,
        "FLT-AIR-9920": 1500,
        "WIDGET-A-100": 900,
        "CNC-INSERT-CNMG432": 12000,
        "PLT-STL-4X8-14GA": 340,
        "TNR-HP-58X": 62,
        "PPR-LTR-20LB": 8800,
        "BLT-HEX-M12-50": 25000,
        "5330-01-234-5678": 90,
        "5310-00-880-7746": 40000,
        "2910-01-441-9902": 6,
    }

    def __init__(self, audit):
        self.audit = audit
        self.calls = []
        self._order_seq = 4400

    def check_inventory(self, part_number):
        self.calls.append({"op": "GET /inventory", "part": part_number})
        available = self.INVENTORY.get(part_number)
        self.audit.log(
            "ERP_INVENTORY_CHECK",
            part=part_number,
            available=available if available is not None else "PART_NOT_FOUND",
            http_status=200 if available is not None else 404,
        )
        return {"part_number": part_number, "available": available, "found": available is not None}

    def create_sales_order(self, order_data):
        self._order_seq += 1
        order_id = f"SO-2026-{self._order_seq}"
        self.calls.append({"op": "POST /salesOrders", "data": order_data})
        self.audit.log(
            "UPSTREAM_ACK", http_status=201,
            resource_id=f"SalesOrder/{order_id}", part=order_data.get("partNumber"),
            quantity=order_data.get("quantity"),
        )
        return {"id": order_id, **order_data}

    def get_order_acknowledgment(self, order_id):
        self.calls.append({"op": "GET /acknowledgment", "order": order_id})
        return {"order_id": order_id, "pages": 1, "format": "application/pdf"}
