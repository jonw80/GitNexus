#!/usr/bin/env python3
"""Render reports/SIMULATION_REPORT.md from a results.json produced by run_simulation.py."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def pct(x):
    return f"{x * 100:.0f}%"


def load(path):
    with open(path) as fh:
        return json.load(fh)


def case_table(results):
    rows = ["| Case | D | Document | Transport | OCR conf | Intent | Disposition | Verdict |",
            "|---|---|---|---|---|---|---|---|"]
    for r in results:
        s = r["scoring"]
        t = r["transport"]
        verdict = "safe" if s["disposition_safe"] else "**UNSAFE**"
        if s["phi_misdirection"]:
            verdict = "**PHI BREACH**"
        elif s["spillage_unhandled"]:
            verdict = "**SPILLAGE**"
        elif s["phantom_order"]:
            verdict = "**PHANTOM ORDER**"
        transport = f"{t['modulation']} {t['bps']//1000}k"
        if t["pages_lost"]:
            transport += f", {t['pages_lost']}pg lost"
        if not t["ecm"]:
            transport += ", no ECM"
        rows.append(
            f"| `{r['case_id']}` | {r['difficulty']} | {r['title']} | {transport} | "
            f"{r['ocr']['avg_confidence']:.3f} | {r['nlu']['intent']} "
            f"({r['nlu']['confidence']:.2f}) | {r['workflow']['disposition']} | {verdict} |"
        )
    return "\n".join(rows)


def gate_table(metrics):
    rows = ["| Criterion | Threshold | Measured | Result |", "|---|---|---|---|"]
    for g in metrics["go_live_gate"].values():
        v = g["value"]
        vs = f"{v:.3f}" if isinstance(v, float) else str(v)
        rows.append(f"| {g['label']} | {g['op']} {g['threshold']} | {vs} | "
                    f"{'PASS' if g['pass'] else '**FAIL**'} |")
    return "\n".join(rows)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "reports", "results.json")
    data = load(src)
    base, hard = data["baseline"], data["hardened"]
    bm, hm = base["metrics"], hard["metrics"]
    br, hr = base["results"], hard["results"]
    by_id = {r["case_id"]: r for r in br}
    hby_id = {r["case_id"]: r for r in hr}

    unsafe = [r for r in br if not r["scoring"]["disposition_safe"]]

    out = []
    w = out.append

    w("# Protocol Box v4.1 — Simulation Fax Run")
    w("")
    w("Twenty synthetic faxes, four verticals (MRO, manufacturer ordering, office, "
      "military), five difficulty tiers each, driven through the eight-stage pipeline "
      "specified in sections 12–14 of the Master Internal Build File.")
    w("")
    w("Each fax is run twice against a byte-identical OCR result: once against the "
      "pipeline exactly as v4.1 specifies it (`baseline`), and once with six proposed "
      "controls enabled (`hardened`). Every difference between the two columns is "
      "attributable to the pipeline change, not to sampling.")
    w("")
    w("## Headline result")
    w("")
    w(f"The pipeline as specified handles **{bm['disposition_safe_rate']*100:.0f}% "
      f"({sum(1 for r in br if r['scoring']['disposition_safe'])} of {len(br)})** "
      "of this corpus safely. The six proposed controls raise that to "
      f"**{hm['disposition_safe_rate']*100:.0f}% "
      f"({sum(1 for r in hr if r['scoring']['disposition_safe'])} of {len(hr)})**.")
    w("")
    w("| Metric | Baseline (v4.1) | Hardened | ")
    w("|---|---|---|")
    for label, key, fmt in [
        ("Intent classification accuracy", "intent_accuracy", "{:.1%}"),
        ("Safe disposition rate", "disposition_safe_rate", "{:.1%}"),
        ("Optimal disposition rate", "disposition_optimal_rate", "{:.1%}"),
        ("Entity extraction accuracy", "entity_accuracy", "{:.1%}"),
        ("Average OCR confidence", "avg_ocr_confidence", "{:.3f}"),
        ("PHI misdirection events", "phi_misdirection_count", "{}"),
        ("Uncontained classified spillage", "spillage_unhandled_count", "{}"),
        ("Phantom ERP orders", "phantom_order_count", "{}"),
        ("TTFA within SKU budget", "ttfa_within_budget_rate", "{:.1%}"),
    ]:
        w(f"| {label} | {fmt.format(bm[key])} | {fmt.format(hm[key])} |")
    w("")
    w("## Section 16.3 Ghost Mode go-live gate")
    w("")
    w("### Baseline")
    w("")
    w(gate_table(bm))
    w("")
    w("### Hardened")
    w("")
    w(gate_table(hm))
    w("")
    w("Neither profile clears the gate. The sample-size criterion (≥100 faxes) cannot "
      "be met by a 20-case corpus by construction; the substantive blockers are intent "
      "accuracy and entity extraction accuracy in both profiles, plus a PHI "
      "misdirection event in baseline.")
    w("")

    w("## Per-vertical results")
    w("")
    w("| Vertical | Baseline safe | Hardened safe | Baseline intent | Hardened intent |")
    w("|---|---|---|---|---|")
    for v in ["MRO", "Manufacturer Ordering", "Office", "Military"]:
        bs = [r for r in br if r["vertical"] == v]
        hs = [r for r in hr if r["vertical"] == v]
        w(f"| {v} | {sum(1 for r in bs if r['scoring']['disposition_safe'])}/{len(bs)} | "
          f"{sum(1 for r in hs if r['scoring']['disposition_safe'])}/{len(hs)} | "
          f"{sum(1 for r in bs if r['scoring']['intent_correct'])}/{len(bs)} | "
          f"{sum(1 for r in hs if r['scoring']['intent_correct'])}/{len(hs)} |")
    w("")
    w("Military is the worst-served vertical in baseline. Nothing in the section 13.2 "
      "taxonomy describes a MILSTRIP requisition or a DD Form 1155 delivery order, and "
      "section 13.4 has no NSN, CAGE code or DODAAC entity type, so defence traffic is "
      "forced through `PURCHASE_ORDER` or the low-confidence fallback.")
    w("")

    w("## Difficulty response — the inversion")
    w("")
    w("| Tier | Baseline safe | Hardened safe | Mean OCR confidence |")
    w("|---|---|---|---|")
    for d in [1, 2, 3, 4, 5]:
        bs = [r for r in br if r["difficulty"] == d]
        hs = [r for r in hr if r["difficulty"] == d]
        oc = sum(r["ocr"]["avg_confidence"] for r in bs) / len(bs)
        w(f"| D{d} | {sum(1 for r in bs if r['scoring']['disposition_safe'])}/{len(bs)} | "
          f"{sum(1 for r in hs if r['scoring']['disposition_safe'])}/{len(hs)} | {oc:.3f} |")
    w("")
    w("Baseline safety does not fall monotonically with difficulty — it is worst in the "
      "middle tiers. Badly degraded faxes (D5) fail the 0.60 confidence threshold and "
      "are parked for an operator, which is the safe outcome. Clean faxes carrying an "
      "intent the taxonomy does not model (D2–D3) are classified confidently and wrongly, "
      "and act on that. **The system is most dangerous when the transport is perfect and "
      "the document is merely unfamiliar.**")
    w("")

    w("## Findings")
    w("")

    findings = [
        ("F-1", "CRITICAL", "PHI released to a law firm with no HIPAA authorization",
         "OFF-05",
         "A subpoena-driven request for an employee's *personnel file* names an "
         "individual who is also a patient in the EMR. The classifier scores it "
         "`RECORDS_REQUEST` at 0.99 on records vocabulary alone, `handleRecordsRequest` "
         "matches the patient on name and date of birth, and three clinical "
         "DocumentReferences are faxed out. The destination is worse than the "
         "disclosure: no `FAX_NUMBER` entity was extracted, so the records went to the "
         "**caller ID** of whoever placed the call. Section 16.3 sets a 0% tolerance "
         "for exactly this event.",
         "Nothing between the classifier and the FHIR client checks whether the "
         "requester is a covered entity, whether an authorization is attached, or "
         "whether the request has any clinical provenance at all. `RECORDS_REQUEST` "
         "confidence is the sole gate on PHI disclosure.",
         "PB-C3 PHI scope guard plus a distinct `LEGAL_RECORDS_REQUEST` class, and "
         "PB-C5 so a PHI payload can never use the caller-ID fallback. Hardened routes "
         "this to a records officer and never queries the EMR."),

        ("F-2", "CRITICAL", "Classified spillage is processed rather than contained",
         "MIL-04",
         "A SECRET//NOFORN transmittal misdialled onto a commercial DID reaches a PB-8 "
         "with no COMSEC bay, no TEMPEST shielding and no Type 1 capability. Baseline "
         "OCRs both pages into the shared-data volume, classifies them, and parks the "
         "result in a human review queue on an unclassified appliance.",
         "There is no classification-banner detector anywhere in sections 12-14. The "
         "low-confidence fallback catches this by accident, not by design, and the "
         "fallback still writes plaintext OCR of classified material to shared "
         "storage. Had the page scored above 0.60 it would have been eligible for an "
         "auto-reply that retransmits classified content over the PSTN.",
         "PB-C1 banner detector running *before* OCR export, sealing the document, "
         "suppressing auto-reply, and alerting the security officer."),

        ("F-3", "HIGH", "Unknown part numbers create phantom sales orders",
         "MIL-02, MFG-02, MIL-03, MRO-04",
         "`processor.js` guards order creation with "
         "`if (inventory.available < entities.QUANTITY)`. When the ERP has no record, "
         "`available` is `undefined`, and `undefined < n` evaluates to `false` in "
         "JavaScript, so the guard passes and the order is created. Four of twenty "
         "baseline runs commit a sales order against a part number the catalogue does "
         "not contain, and fax an acknowledgment for goods that can never ship. "
         "A single character is enough: `MIL-02` read NSN `5330-01-234-5678` as "
         "`S330-01-234-5678` at a 1.2% character error rate and ordered 1,200 gaskets "
         "against it; `MIL-03` turned the digit 1 into a letter l.",
         "The lookup failure is never surfaced. Nothing distinguishes 'part exists and "
         "has stock' from 'part does not exist', because both take the same branch.",
         "PB-C6 explicit `found` check. In the shipped code the fix is to test "
         "`inventory.available === undefined || inventory.available < qty`."),

        ("F-4", "HIGH", "Multi-line orders are silently truncated to line one",
         "MFG-02",
         "A four-line blanket order worth $214,800 is classified `PURCHASE_ORDER` at "
         "0.99 and converted into a single sales order for line 1 only. Lines 2-4 are "
         "discarded with no error, no warning, and no audit entry. The acknowledgment "
         "faxed back confirms the order, so the customer believes all four lines were "
         "accepted.",
         "Section 13.4's entity model is flat: one `PART_NUMBER`, one `QUANTITY`, one "
         "`PO_NUMBER` per document, and `handlePurchaseOrder` consumes exactly that "
         "shape. Blanket orders and scheduled releases are the normal form of "
         "manufacturer ordering, not an edge case.",
         "Line-item extraction with an explicit line count, and a hard rule that any "
         "document whose line count exceeds one goes to review until the data model "
         "supports it."),

        ("F-5", "HIGH", "A PO revision books a second order at the pre-revision quantity",
         "MFG-03",
         "A revision headed *SUPERSEDES ALL PREVIOUS VERSIONS* that cuts quantity from "
         "250 to 175 is read at a 0.3% character error rate, classified "
         "`PURCHASE_ORDER` at 0.997, and booked as a **new** order for **250** units. "
         "The extractor anchored on the `Original Quantity:` line and never saw "
         "`Revised Quantity:`. The customer asked to reduce an order to 175 and ends "
         "up holding 500 units across two acknowledged orders.",
         "This is the corpus's clearest example of the difficulty inversion: near "
         "perfect OCR, high classifier confidence, and the worst commercial outcome in "
         "the run. Accuracy on the page bought nothing because the taxonomy has no "
         "concept of supersession.",
         "`ORDER_CHANGE` class plus a duplicate-PO check against open orders, and "
         "field extraction that prefers the most specific label on a line."),

        ("F-6", "HIGH", "Non-order documents that mention parts become orders",
         "OFF-02, MRO-03",
         "An invoice (`OFF-02`) and an RFQ explicitly headed *THIS IS NOT AN ORDER* "
         "(`MRO-03`) both classify as `PURCHASE_ORDER` in baseline and both create ERP "
         "sales orders. The invoice re-orders 12 toner cartridges that have already "
         "shipped and been billed; the RFQ books 500 filter elements for a customer "
         "who asked only for pricing.",
         "Section 13.2 ships seven classes, five of them clinical. Every industrial, "
         "office and defence document that is not literally a purchase order has no "
         "correct destination, and `PURCHASE_ORDER` is the nearest attractor for "
         "anything containing a part number and a quantity.",
         "PB-C2 extended taxonomy: `RFQ_QUOTE`, `ORDER_CHANGE`, `INVOICE_REMITTANCE`, "
         "`MRO_WORK_ORDER`, `MILSTRIP_REQUISITION`, `CONTRACT_DOCUMENT`, "
         "`LEGAL_RECORDS_REQUEST`."),

        ("F-7", "HIGH", "Defence documents are accepted as commercial sales orders",
         "MIL-01, MIL-02, MIL-03",
         "A DD Form 1348-1A requisition for 5,000 washers, a priority-03 NMCS "
         "requisition for six fuel pumps, and a DFARS delivery order for 1,200 gaskets "
         "all classify as `PURCHASE_ORDER` and all create ERP sales orders keyed on "
         "the NSN.",
         "`MIL-02` is the serious one. Accepting a DD Form 1155 as an ordinary sales "
         "order constitutes acceptance of the clauses it incorporates, including DFARS "
         "252.204-7012 (safeguarding covered defence information) and 252.246-7007 "
         "(counterfeit part detection). The document says so in terms: *acceptance "
         "constitutes agreement to all clauses incorporated above*. No automated "
         "system is authorised to accept those on a contractor's behalf, and the "
         "appliance did it in under 12 seconds.",
         "`MILSTRIP_REQUISITION` and `CONTRACT_DOCUMENT` classes with NSN, CAGE and "
         "DODAAC entity types; contract documents always route to contract "
         "administration and never auto-acknowledge."),

        ("F-8", "MEDIUM", "Entity confidence is gated on the document average, not the field",
         "MRO-04",
         "A handwritten requisition averages 0.735 OCR confidence, comfortably above "
         "the 0.60 floor, while the part number itself is read at **0.32**. Baseline "
         "creates an order for `WSH-FT-Ml` (the operator wrote `BLT-HEX-M12-50`) in a "
         "quantity of **3** (the operator wrote 300).",
         "Section 12.3 defines one confidence threshold for the whole document. "
         "Handwritten forms are precisely where the average hides the failure: the "
         "printed labels are clean and carry the token count, and the handwritten "
         "values that actually matter are not.",
         "PB-C4 per-entity confidence floor on order-critical fields, plus a quantity "
         "sanity check. Hardened stops this case on the 0.32 part-number confidence."),

        ("F-9", "MEDIUM", "OCR damage to a *label* silently discards the value",
         "MFG-04",
         "At a 6.1% character error rate `Part Number:` is read as `Part Numbr:`. The "
         "entity pattern anchors on the label, so `PLT-STL-4X8-14GA` is lost entirely "
         "even though the value itself was legible on the page.",
         "The failure is safe here, but the mechanism is not rare. Label strings run "
         "10-14 characters, so label damage rather than value damage accounts for a "
         "meaningful share of extraction misses, and it is invisible in any metric "
         "based on document-level confidence.",
         "Fuzzy label matching and a positional fallback that accepts a value-shaped "
         "token adjacent to a damaged label."),

        ("F-10", "MEDIUM", "Reply faxes fall back to caller ID without verification",
         "OFF-05, OFF-02, MRO-04",
         "Three baseline runs sent their reply to the calling number because no "
         "`FAX_NUMBER` entity survived extraction. For an order acknowledgment that is "
         "usually harmless. For `OFF-05` it means patient records were faxed to an "
         "unverified number.",
         "Section 14.3 passes `entities.FAX_NUMBER` straight to `faxSender.send()` "
         "with no null check, so in the shipped code an undefined destination is an "
         "uncontrolled runtime failure rather than a routing decision.",
         "PB-C5 reply-path guard: PHI payloads require an extracted fax-back number "
         "and caller-ID fallback is never sufficient."),

        ("F-11", "MEDIUM", "Entity patterns fire on unrelated text",
         "MIL-03, MIL-02, MFG-04",
         "`MIL-03`, a defence requisition with no person named anywhere on it, "
         "produced `PATIENT_NAME: DSN`. `MIL-02` produced `PO_NUMBER: RATED` from the "
         "word *incorporated*; `MFG-04` produced `FACILITY_NAME: Cascade Metalworks "
         "0nc`.",
         "The patterns have no negative evidence and no validation of the captured "
         "shape. A spurious `PATIENT_NAME` is not harmless: combined with F-1, a "
         "document that classifies as `RECORDS_REQUEST` for any reason will carry a "
         "fabricated patient name into a live EMR query.",
         "Validate captured values against a shape grammar per entity type, and "
         "suppress clinical entity types on documents whose DID class is not "
         "clinical."),

        ("F-12", "LOW", "Three intent classes have no handler in the orchestrator",
         None,
         "Section 13.2 defines actions for `LAB_RESULT` (route to provider inbox), "
         "`PRESCRIPTION_REFILL` (route to pharmacy queue) and `INSURANCE_DENIAL` "
         "(route to billing). The `switch` in section 14.3 has cases only for "
         "`RECORDS_REQUEST`, `PURCHASE_ORDER`, `CLARIFICATION_NEEDED` and "
         "`SPAM_OTHER`. All three fall through to `default: routeToHumanReview`.",
         "Three of the seven shipped classes cannot reach their documented action. "
         "The classifier can be perfectly accurate on them and the routing will still "
         "be wrong. No case in this corpus exercises them, so the defect is invisible "
         "to a healthcare-only test set as well.",
         "Add the missing cases, or remove the classes from section 13.2 until they "
         "are wired."),

        ("F-13", "LOW", "TTFA budget is exceeded on multi-page degraded faxes",
         "MRO-05, MFG-04, OFF-04",
         "Three of twenty runs exceed the SKU time-to-first-action budget. `MRO-05` "
         "reaches 35.6s against a 25s PB-8 budget; `MFG-04` and `OFF-04` exceed the "
         "30s PB-4 budget. All three are multi-page faxes carrying heavy preprocessing "
         "load.",
         "The section 3.2 and 4.2 TTFA figures are quoted without qualification. They "
         "hold for a clean single page and do not hold for the degraded multi-page "
         "traffic that dominates MRO and defence.",
         "Restate TTFA per page and per quality tier, or raise the published budget."),

        ("F-14", "INFO", "Page loss is invisible in the audit trail",
         "MRO-05, MIL-05",
         "Two faxes lost a page in transit. In both cases the audit log records a "
         "successful reception with a valid SHA-256 seal, because T.30 confirms the "
         "pages that arrived rather than the pages that were sent. `MRO-05`'s cover "
         "sheet says *4 PAGES INCLUDING THIS ONE* and the replacement parts list is "
         "the page that never arrived.",
         "The section 22 chain-of-evidence argument rests on the seal proving "
         "integrity of the original. It proves integrity of what was received, which "
         "is a weaker claim than the legal-admissibility framing implies.",
         "Parse the declared page count from the cover sheet where present and "
         "reconcile it against pages received; log a discrepancy explicitly."),
    ]

    for fid, sev, title, cases, body, why, fix in findings:
        w(f"### {fid} — {title}")
        w("")
        meta = [f"**Severity:** {sev}"]
        if cases:
            meta.append(f"**Cases:** `{cases}`")
        w("  ·  ".join(meta))
        w("")
        fmt = {}
        if cases and "," not in (cases or ""):
            r = by_id.get(cases)
            if r:
                fmt = {
                    "conf": r["nlu"]["confidence"],
                    "ocr": r["ocr"]["avg_confidence"],
                }
        fmt.setdefault("conf", 0.0)
        fmt.setdefault("ocr", 0.0)
        fmt["phantom"] = bm["phantom_order_count"]
        fmt["ttfa_rate"] = bm["ttfa_within_budget_rate"]
        w(body.format(**fmt))
        w("")
        w(f"**Why it happens.** {why.format(**fmt)}")
        w("")
        w(f"**Mitigation.** {fix}")
        w("")

    w("## Proposed controls")
    w("")
    w("| ID | Control | Addresses |")
    w("|---|---|---|")
    for cid, name, addresses in [
        ("PB-C1", "Classification banner detector, pre-OCR-export", "F-2"),
        ("PB-C2", "Extended intent taxonomy (7 new classes)", "F-5, F-6, F-7"),
        ("PB-C3", "PHI scope guard on the EMR path", "F-1"),
        ("PB-C4", "Per-entity confidence floor on order-critical fields", "F-8"),
        ("PB-C5", "Reply-path guard for PHI payloads", "F-10"),
        ("PB-C6", "Explicit unknown-part check before order creation", "F-3"),
    ]:
        w(f"| `{cid}` | {name} | {addresses} |")
    w("")
    fired = {}
    for r in hr:
        for c in r["controls_fired"]:
            fired.setdefault(c, []).append(r["case_id"])
    w("Controls that fired in the hardened run:")
    w("")
    for c, ids in sorted(fired.items()):
        w(f"- `{c}` — {', '.join(ids)}")
    w("")
    w("### What the controls cost")
    w("")
    w("Adding classes dilutes softmax mass on hybrid documents. `MRO-02`, an emergency "
      "breakdown that is simultaneously a work order and a purchase order, moves from a "
      "confident `PURCHASE_ORDER` in baseline to `MRO_WORK_ORDER` in hardened and routes "
      "to CMMS instead of triggering an inventory check. The outcome is still safe, but "
      "it is the one case where the hardened profile is less correct than baseline, and "
      "it is the reason hardened intent accuracy is "
      f"{hm['intent_accuracy']:.0%} rather than higher.")
    w("")
    w("Guards also convert successful automation into review work. Hardened drops from "
      f"{sum(1 for r in br if r['workflow']['disposition'] == 'AUTO_ACTION')} to "
      f"{sum(1 for r in hr if r['workflow']['disposition'] == 'AUTO_ACTION')} "
      "closed-loop auto-actions across the corpus. Every one of the suppressed "
      "auto-actions was wrong, so this is the intended trade, but it is a real change "
      "to the labour model the section 1.4 ROI case rests on.")
    w("")

    w("## Case-by-case detail")
    w("")
    w("### Baseline")
    w("")
    w(case_table(br))
    w("")
    w("### Hardened")
    w("")
    w(case_table(hr))
    w("")

    w("## Transport observations")
    w("")
    lost = [r for r in br if r["transport"]["pages_lost"]]
    noecm = [r for r in br if not r["transport"]["ecm"]]
    w(f"- {len(lost)} of {len(br)} faxes lost at least one page in transit "
      f"({', '.join(r['case_id'] for r in lost)}). In every case the audit log records "
      "a successful reception, because T.30 confirms the pages it received, not the "
      "pages that were sent. A recipient reading the log cannot tell that `MRO-05`'s "
      "parts list never arrived.")
    w(f"- {len(noecm)} fax negotiated ECM off "
      f"({', '.join(r['case_id'] for r in noecm) or 'none'}), so page errors became "
      "permanent scanline damage rather than retransmissions.")
    w("- The modulation ladder behaved as specified: V.34 on clean lines down to "
      "V.27ter at 4.8 kbps on the tactical circuit, where a 3-page fax took "
      f"{max(r['transport']['transfer_sec'] for r in br):.0f} seconds to transfer.")
    w("- Audit hash chains verified intact on "
      f"{sum(1 for r in br if r['audit']['chain_valid'])}/{len(br)} runs.")
    w("")

    w("## Reproducing")
    w("")
    w("```bash")
    w("cd protocol-box-sim")
    w("python3 run_simulation.py --json reports/results.json")
    w("python3 generate_report.py")
    w("")
    w("python3 run_simulation.py --profile baseline --case OFF-05 -v   # audit log")
    w("python3 run_simulation.py --vertical Military --no-color")
    w("```")
    w("")
    w("Runs are deterministic under a fixed `--seed` (default 20260314). Transport and "
      "OCR draw an identical random stream in both profiles.")

    dest = os.path.join(HERE, "reports", "SIMULATION_REPORT.md")
    with open(dest, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
