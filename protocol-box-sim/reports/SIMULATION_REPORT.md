# Protocol Box v4.1 — Simulation Fax Run

Twenty synthetic faxes, four verticals (MRO, manufacturer ordering, office, military), five difficulty tiers each, driven through the eight-stage pipeline specified in sections 12–14 of the Master Internal Build File.

Each fax is run twice against a byte-identical OCR result: once against the pipeline exactly as v4.1 specifies it (`baseline`), and once with six proposed controls enabled (`hardened`). Every difference between the two columns is attributable to the pipeline change, not to sampling.

## Headline result

The pipeline as specified handles **50% (10 of 20)** of this corpus safely. The six proposed controls raise that to **95% (19 of 20)**.

| Metric | Baseline (v4.1) | Hardened | 
|---|---|---|
| Intent classification accuracy | 60.0% | 90.0% |
| Safe disposition rate | 50.0% | 95.0% |
| Optimal disposition rate | 45.0% | 85.0% |
| Entity extraction accuracy | 76.7% | 76.7% |
| Average OCR confidence | 0.884 | 0.884 |
| PHI misdirection events | 1 | 0 |
| Uncontained classified spillage | 1 | 0 |
| Phantom ERP orders | 4 | 0 |
| TTFA within SKU budget | 85.0% | 85.0% |

## Section 16.3 Ghost Mode go-live gate

### Baseline

| Criterion | Threshold | Measured | Result |
|---|---|---|---|
| Intent classification accuracy | >= 0.95 | 0.600 | **FAIL** |
| Entity extraction accuracy | >= 0.9 | 0.767 | **FAIL** |
| False positive rate (PHI misdirection) | == 0.0 | 0.050 | **FAIL** |
| OCR confidence (average) | >= 0.85 | 0.884 | PASS |
| Minimum sample size | >= 100 | 20 | **FAIL** |

### Hardened

| Criterion | Threshold | Measured | Result |
|---|---|---|---|
| Intent classification accuracy | >= 0.95 | 0.900 | **FAIL** |
| Entity extraction accuracy | >= 0.9 | 0.767 | **FAIL** |
| False positive rate (PHI misdirection) | == 0.0 | 0.000 | PASS |
| OCR confidence (average) | >= 0.85 | 0.884 | PASS |
| Minimum sample size | >= 100 | 20 | **FAIL** |

Neither profile clears the gate. The sample-size criterion (≥100 faxes) cannot be met by a 20-case corpus by construction; the substantive blockers are intent accuracy and entity extraction accuracy in both profiles, plus a PHI misdirection event in baseline.

## Per-vertical results

| Vertical | Baseline safe | Hardened safe | Baseline intent | Hardened intent |
|---|---|---|---|---|
| MRO | 3/5 | 4/5 | 3/5 | 4/5 |
| Manufacturer Ordering | 3/5 | 5/5 | 4/5 | 4/5 |
| Office | 3/5 | 5/5 | 3/5 | 5/5 |
| Military | 1/5 | 5/5 | 2/5 | 5/5 |

Military is the worst-served vertical in baseline. Nothing in the section 13.2 taxonomy describes a MILSTRIP requisition or a DD Form 1155 delivery order, and section 13.4 has no NSN, CAGE code or DODAAC entity type, so defence traffic is forced through `PURCHASE_ORDER` or the low-confidence fallback.

## Difficulty response — the inversion

| Tier | Baseline safe | Hardened safe | Mean OCR confidence |
|---|---|---|---|
| D1 | 3/4 | 4/4 | 0.974 |
| D2 | 1/4 | 3/4 | 0.962 |
| D3 | 1/4 | 4/4 | 0.966 |
| D4 | 2/4 | 4/4 | 0.836 |
| D5 | 3/4 | 4/4 | 0.684 |

Baseline safety does not fall monotonically with difficulty — it is worst in the middle tiers. Badly degraded faxes (D5) fail the 0.60 confidence threshold and are parked for an operator, which is the safe outcome. Clean faxes carrying an intent the taxonomy does not model (D2–D3) are classified confidently and wrongly, and act on that. **The system is most dangerous when the transport is perfect and the document is merely unfamiliar.**

## Findings

### F-1 — PHI released to a law firm with no HIPAA authorization

**Severity:** CRITICAL  ·  **Cases:** `OFF-05`

A subpoena-driven request for an employee's *personnel file* names an individual who is also a patient in the EMR. The classifier scores it `RECORDS_REQUEST` at 0.99 on records vocabulary alone, `handleRecordsRequest` matches the patient on name and date of birth, and three clinical DocumentReferences are faxed out. The destination is worse than the disclosure: no `FAX_NUMBER` entity was extracted, so the records went to the **caller ID** of whoever placed the call. Section 16.3 sets a 0% tolerance for exactly this event.

**Why it happens.** Nothing between the classifier and the FHIR client checks whether the requester is a covered entity, whether an authorization is attached, or whether the request has any clinical provenance at all. `RECORDS_REQUEST` confidence is the sole gate on PHI disclosure.

**Mitigation.** PB-C3 PHI scope guard plus a distinct `LEGAL_RECORDS_REQUEST` class, and PB-C5 so a PHI payload can never use the caller-ID fallback. Hardened routes this to a records officer and never queries the EMR.

### F-2 — Classified spillage is processed rather than contained

**Severity:** CRITICAL  ·  **Cases:** `MIL-04`

A SECRET//NOFORN transmittal misdialled onto a commercial DID reaches a PB-8 with no COMSEC bay, no TEMPEST shielding and no Type 1 capability. Baseline OCRs both pages into the shared-data volume, classifies them, and parks the result in a human review queue on an unclassified appliance.

**Why it happens.** There is no classification-banner detector anywhere in sections 12-14. The low-confidence fallback catches this by accident, not by design, and the fallback still writes plaintext OCR of classified material to shared storage. Had the page scored above 0.60 it would have been eligible for an auto-reply that retransmits classified content over the PSTN.

**Mitigation.** PB-C1 banner detector running *before* OCR export, sealing the document, suppressing auto-reply, and alerting the security officer.

### F-3 — Unknown part numbers create phantom sales orders

**Severity:** HIGH  ·  **Cases:** `MIL-02, MFG-02, MIL-03, MRO-04`

`processor.js` guards order creation with `if (inventory.available < entities.QUANTITY)`. When the ERP has no record, `available` is `undefined`, and `undefined < n` evaluates to `false` in JavaScript, so the guard passes and the order is created. Four of twenty baseline runs commit a sales order against a part number the catalogue does not contain, and fax an acknowledgment for goods that can never ship. A single character is enough: `MIL-02` read NSN `5330-01-234-5678` as `S330-01-234-5678` at a 1.2% character error rate and ordered 1,200 gaskets against it; `MIL-03` turned the digit 1 into a letter l.

**Why it happens.** The lookup failure is never surfaced. Nothing distinguishes 'part exists and has stock' from 'part does not exist', because both take the same branch.

**Mitigation.** PB-C6 explicit `found` check. In the shipped code the fix is to test `inventory.available === undefined || inventory.available < qty`.

### F-4 — Multi-line orders are silently truncated to line one

**Severity:** HIGH  ·  **Cases:** `MFG-02`

A four-line blanket order worth $214,800 is classified `PURCHASE_ORDER` at 0.99 and converted into a single sales order for line 1 only. Lines 2-4 are discarded with no error, no warning, and no audit entry. The acknowledgment faxed back confirms the order, so the customer believes all four lines were accepted.

**Why it happens.** Section 13.4's entity model is flat: one `PART_NUMBER`, one `QUANTITY`, one `PO_NUMBER` per document, and `handlePurchaseOrder` consumes exactly that shape. Blanket orders and scheduled releases are the normal form of manufacturer ordering, not an edge case.

**Mitigation.** Line-item extraction with an explicit line count, and a hard rule that any document whose line count exceeds one goes to review until the data model supports it.

### F-5 — A PO revision books a second order at the pre-revision quantity

**Severity:** HIGH  ·  **Cases:** `MFG-03`

A revision headed *SUPERSEDES ALL PREVIOUS VERSIONS* that cuts quantity from 250 to 175 is read at a 0.3% character error rate, classified `PURCHASE_ORDER` at 0.997, and booked as a **new** order for **250** units. The extractor anchored on the `Original Quantity:` line and never saw `Revised Quantity:`. The customer asked to reduce an order to 175 and ends up holding 500 units across two acknowledged orders.

**Why it happens.** This is the corpus's clearest example of the difficulty inversion: near perfect OCR, high classifier confidence, and the worst commercial outcome in the run. Accuracy on the page bought nothing because the taxonomy has no concept of supersession.

**Mitigation.** `ORDER_CHANGE` class plus a duplicate-PO check against open orders, and field extraction that prefers the most specific label on a line.

### F-6 — Non-order documents that mention parts become orders

**Severity:** HIGH  ·  **Cases:** `OFF-02, MRO-03`

An invoice (`OFF-02`) and an RFQ explicitly headed *THIS IS NOT AN ORDER* (`MRO-03`) both classify as `PURCHASE_ORDER` in baseline and both create ERP sales orders. The invoice re-orders 12 toner cartridges that have already shipped and been billed; the RFQ books 500 filter elements for a customer who asked only for pricing.

**Why it happens.** Section 13.2 ships seven classes, five of them clinical. Every industrial, office and defence document that is not literally a purchase order has no correct destination, and `PURCHASE_ORDER` is the nearest attractor for anything containing a part number and a quantity.

**Mitigation.** PB-C2 extended taxonomy: `RFQ_QUOTE`, `ORDER_CHANGE`, `INVOICE_REMITTANCE`, `MRO_WORK_ORDER`, `MILSTRIP_REQUISITION`, `CONTRACT_DOCUMENT`, `LEGAL_RECORDS_REQUEST`.

### F-7 — Defence documents are accepted as commercial sales orders

**Severity:** HIGH  ·  **Cases:** `MIL-01, MIL-02, MIL-03`

A DD Form 1348-1A requisition for 5,000 washers, a priority-03 NMCS requisition for six fuel pumps, and a DFARS delivery order for 1,200 gaskets all classify as `PURCHASE_ORDER` and all create ERP sales orders keyed on the NSN.

**Why it happens.** `MIL-02` is the serious one. Accepting a DD Form 1155 as an ordinary sales order constitutes acceptance of the clauses it incorporates, including DFARS 252.204-7012 (safeguarding covered defence information) and 252.246-7007 (counterfeit part detection). The document says so in terms: *acceptance constitutes agreement to all clauses incorporated above*. No automated system is authorised to accept those on a contractor's behalf, and the appliance did it in under 12 seconds.

**Mitigation.** `MILSTRIP_REQUISITION` and `CONTRACT_DOCUMENT` classes with NSN, CAGE and DODAAC entity types; contract documents always route to contract administration and never auto-acknowledge.

### F-8 — Entity confidence is gated on the document average, not the field

**Severity:** MEDIUM  ·  **Cases:** `MRO-04`

A handwritten requisition averages 0.735 OCR confidence, comfortably above the 0.60 floor, while the part number itself is read at **0.32**. Baseline creates an order for `WSH-FT-Ml` (the operator wrote `BLT-HEX-M12-50`) in a quantity of **3** (the operator wrote 300).

**Why it happens.** Section 12.3 defines one confidence threshold for the whole document. Handwritten forms are precisely where the average hides the failure: the printed labels are clean and carry the token count, and the handwritten values that actually matter are not.

**Mitigation.** PB-C4 per-entity confidence floor on order-critical fields, plus a quantity sanity check. Hardened stops this case on the 0.32 part-number confidence.

### F-9 — OCR damage to a *label* silently discards the value

**Severity:** MEDIUM  ·  **Cases:** `MFG-04`

At a 6.1% character error rate `Part Number:` is read as `Part Numbr:`. The entity pattern anchors on the label, so `PLT-STL-4X8-14GA` is lost entirely even though the value itself was legible on the page.

**Why it happens.** The failure is safe here, but the mechanism is not rare. Label strings run 10-14 characters, so label damage rather than value damage accounts for a meaningful share of extraction misses, and it is invisible in any metric based on document-level confidence.

**Mitigation.** Fuzzy label matching and a positional fallback that accepts a value-shaped token adjacent to a damaged label.

### F-10 — Reply faxes fall back to caller ID without verification

**Severity:** MEDIUM  ·  **Cases:** `OFF-05, OFF-02, MRO-04`

Three baseline runs sent their reply to the calling number because no `FAX_NUMBER` entity survived extraction. For an order acknowledgment that is usually harmless. For `OFF-05` it means patient records were faxed to an unverified number.

**Why it happens.** Section 14.3 passes `entities.FAX_NUMBER` straight to `faxSender.send()` with no null check, so in the shipped code an undefined destination is an uncontrolled runtime failure rather than a routing decision.

**Mitigation.** PB-C5 reply-path guard: PHI payloads require an extracted fax-back number and caller-ID fallback is never sufficient.

### F-11 — Entity patterns fire on unrelated text

**Severity:** MEDIUM  ·  **Cases:** `MIL-03, MIL-02, MFG-04`

`MIL-03`, a defence requisition with no person named anywhere on it, produced `PATIENT_NAME: DSN`. `MIL-02` produced `PO_NUMBER: RATED` from the word *incorporated*; `MFG-04` produced `FACILITY_NAME: Cascade Metalworks 0nc`.

**Why it happens.** The patterns have no negative evidence and no validation of the captured shape. A spurious `PATIENT_NAME` is not harmless: combined with F-1, a document that classifies as `RECORDS_REQUEST` for any reason will carry a fabricated patient name into a live EMR query.

**Mitigation.** Validate captured values against a shape grammar per entity type, and suppress clinical entity types on documents whose DID class is not clinical.

### F-12 — Three intent classes have no handler in the orchestrator

**Severity:** LOW

Section 13.2 defines actions for `LAB_RESULT` (route to provider inbox), `PRESCRIPTION_REFILL` (route to pharmacy queue) and `INSURANCE_DENIAL` (route to billing). The `switch` in section 14.3 has cases only for `RECORDS_REQUEST`, `PURCHASE_ORDER`, `CLARIFICATION_NEEDED` and `SPAM_OTHER`. All three fall through to `default: routeToHumanReview`.

**Why it happens.** Three of the seven shipped classes cannot reach their documented action. The classifier can be perfectly accurate on them and the routing will still be wrong. No case in this corpus exercises them, so the defect is invisible to a healthcare-only test set as well.

**Mitigation.** Add the missing cases, or remove the classes from section 13.2 until they are wired.

### F-13 — TTFA budget is exceeded on multi-page degraded faxes

**Severity:** LOW  ·  **Cases:** `MRO-05, MFG-04, OFF-04`

Three of twenty runs exceed the SKU time-to-first-action budget. `MRO-05` reaches 35.6s against a 25s PB-8 budget; `MFG-04` and `OFF-04` exceed the 30s PB-4 budget. All three are multi-page faxes carrying heavy preprocessing load.

**Why it happens.** The section 3.2 and 4.2 TTFA figures are quoted without qualification. They hold for a clean single page and do not hold for the degraded multi-page traffic that dominates MRO and defence.

**Mitigation.** Restate TTFA per page and per quality tier, or raise the published budget.

### F-14 — Page loss is invisible in the audit trail

**Severity:** INFO  ·  **Cases:** `MRO-05, MIL-05`

Two faxes lost a page in transit. In both cases the audit log records a successful reception with a valid SHA-256 seal, because T.30 confirms the pages that arrived rather than the pages that were sent. `MRO-05`'s cover sheet says *4 PAGES INCLUDING THIS ONE* and the replacement parts list is the page that never arrived.

**Why it happens.** The section 22 chain-of-evidence argument rests on the seal proving integrity of the original. It proves integrity of what was received, which is a weaker claim than the legal-admissibility framing implies.

**Mitigation.** Parse the declared page count from the cover sheet where present and reconcile it against pages received; log a discrepancy explicitly.

## Proposed controls

| ID | Control | Addresses |
|---|---|---|
| `PB-C1` | Classification banner detector, pre-OCR-export | F-2 |
| `PB-C2` | Extended intent taxonomy (7 new classes) | F-5, F-6, F-7 |
| `PB-C3` | PHI scope guard on the EMR path | F-1 |
| `PB-C4` | Per-entity confidence floor on order-critical fields | F-8 |
| `PB-C5` | Reply-path guard for PHI payloads | F-10 |
| `PB-C6` | Explicit unknown-part check before order creation | F-3 |

Controls that fired in the hardened run:

- `PB-C1 spillage guard` — MIL-04
- `PB-C2 extended taxonomy` — MRO-02, MRO-03, OFF-02, OFF-04, OFF-05, MIL-01, MIL-02, MIL-03
- `PB-C4 entity confidence floor` — MRO-04, MFG-04, MFG-05
- `PB-C6 unknown-part guard` — MFG-02

### What the controls cost

Adding classes dilutes softmax mass on hybrid documents. `MRO-02`, an emergency breakdown that is simultaneously a work order and a purchase order, moves from a confident `PURCHASE_ORDER` in baseline to `MRO_WORK_ORDER` in hardened and routes to CMMS instead of triggering an inventory check. The outcome is still safe, but it is the one case where the hardened profile is less correct than baseline, and it is the reason hardened intent accuracy is 90% rather than higher.

Guards also convert successful automation into review work. Hardened drops from 12 to 3 closed-loop auto-actions across the corpus. Every one of the suppressed auto-actions was wrong, so this is the intended trade, but it is a real change to the labour model the section 1.4 ROI case rests on.

## Case-by-case detail

### Baseline

| Case | D | Document | Transport | OCR conf | Intent | Disposition | Verdict |
|---|---|---|---|---|---|---|---|
| `MRO-01` | 1 | Routine MRO stores replenishment order | V.34 33k | 0.975 | PURCHASE_ORDER (1.00) | AUTO_ACTION | safe |
| `MRO-02` | 2 | Emergency breakdown expedite - quantity exceeds stock | V.17 14k | 0.959 | PURCHASE_ORDER (0.97) | HUMAN_REVIEW | safe |
| `MRO-03` | 3 | Preventive maintenance RFQ - explicitly not an order | V.34 33k | 0.975 | PURCHASE_ORDER (0.99) | AUTO_ACTION | **UNSAFE** |
| `MRO-04` | 4 | Handwritten field technician parts requisition | V.17 14k | 0.735 | PURCHASE_ORDER (0.97) | AUTO_ACTION | **PHANTOM ORDER** |
| `MRO-05` | 5 | Compound fax: failure report + warranty claim + parts list, page lost | V.27ter 4k, 1pg lost | 0.624 | PURCHASE_ORDER (0.80) | HUMAN_REVIEW | safe |
| `MFG-01` | 1 | Clean single-line production purchase order | V.34 33k | 0.974 | PURCHASE_ORDER (1.00) | AUTO_ACTION | safe |
| `MFG-02` | 2 | Four-line blanket order with scheduled releases | V.34 33k | 0.969 | PURCHASE_ORDER (0.99) | AUTO_ACTION | **PHANTOM ORDER** |
| `MFG-03` | 3 | PO revision superseding a previously transmitted order | V.34 33k | 0.974 | PURCHASE_ORDER (1.00) | AUTO_ACTION | **UNSAFE** |
| `MFG-04` | 4 | Degraded order exceeding available stock | V.29 9k | 0.890 | PURCHASE_ORDER (0.99) | HUMAN_REVIEW | safe |
| `MFG-05` | 5 | Bilingual supplier PO, unknown part, no reply fax number | V.29 9k | 0.708 | PURCHASE_ORDER (0.96) | HUMAN_REVIEW | safe |
| `OFF-01` | 1 | Office supply reorder | V.34 33k | 0.974 | PURCHASE_ORDER (1.00) | AUTO_ACTION | safe |
| `OFF-02` | 2 | Vendor invoice and remittance advice | V.34 33k | 0.961 | PURCHASE_ORDER (0.89) | AUTO_ACTION | **UNSAFE** |
| `OFF-03` | 3 | Unsolicited advertising fax | V.17 14k | 0.963 | SPAM_OTHER (0.99) | ARCHIVE | safe |
| `OFF-04` | 4 | Executed service agreement signature page | V.29 9k | 0.760 | CLARIFICATION_NEEDED (0.45) | HUMAN_REVIEW | safe |
| `OFF-05` | 5 | Law firm employment-records request naming a real patient | V.17 14k | 0.975 | RECORDS_REQUEST (0.99) | AUTO_ACTION | **PHI BREACH** |
| `MIL-01` | 1 | Routine MILSTRIP requisition, DD Form 1348-1A | V.34 33k | 0.973 | PURCHASE_ORDER (0.91) | AUTO_ACTION | **UNSAFE** |
| `MIL-02` | 2 | Contract delivery order, DD Form 1155 with DFARS flow-downs | V.17 14k | 0.961 | PURCHASE_ORDER (0.97) | AUTO_ACTION | **PHANTOM ORDER** |
| `MIL-03` | 3 | Priority 03 casualty requisition, stock exactly equal to demand | V.17 14k | 0.950 | PURCHASE_ORDER (0.93) | AUTO_ACTION | **PHANTOM ORDER** |
| `MIL-04` | 4 | SECRET//NOFORN marked page delivered to an unclassified DID | V.17 14k | 0.959 | CLARIFICATION_NEEDED (0.35) | HUMAN_REVIEW | **SPILLAGE** |
| `MIL-05` | 5 | Field-expedient requisition over a degraded tactical circuit | V.27ter 4k, 1pg lost, no ECM | 0.428 | CLARIFICATION_NEEDED (0.19) | HUMAN_REVIEW | safe |

### Hardened

| Case | D | Document | Transport | OCR conf | Intent | Disposition | Verdict |
|---|---|---|---|---|---|---|---|
| `MRO-01` | 1 | Routine MRO stores replenishment order | V.34 33k | 0.975 | PURCHASE_ORDER (1.00) | AUTO_ACTION | safe |
| `MRO-02` | 2 | Emergency breakdown expedite - quantity exceeds stock | V.17 14k | 0.959 | MRO_WORK_ORDER (0.85) | ROUTE | **UNSAFE** |
| `MRO-03` | 3 | Preventive maintenance RFQ - explicitly not an order | V.34 33k | 0.975 | RFQ_QUOTE (0.96) | ROUTE | safe |
| `MRO-04` | 4 | Handwritten field technician parts requisition | V.17 14k | 0.735 | PURCHASE_ORDER (0.87) | HUMAN_REVIEW | safe |
| `MRO-05` | 5 | Compound fax: failure report + warranty claim + parts list, page lost | V.27ter 4k, 1pg lost | 0.624 | CLARIFICATION_NEEDED (0.44) | HUMAN_REVIEW | safe |
| `MFG-01` | 1 | Clean single-line production purchase order | V.34 33k | 0.974 | PURCHASE_ORDER (1.00) | AUTO_ACTION | safe |
| `MFG-02` | 2 | Four-line blanket order with scheduled releases | V.34 33k | 0.969 | PURCHASE_ORDER (0.98) | HUMAN_REVIEW | safe |
| `MFG-03` | 3 | PO revision superseding a previously transmitted order | V.34 33k | 0.974 | CLARIFICATION_NEEDED (0.51) | HUMAN_REVIEW | safe |
| `MFG-04` | 4 | Degraded order exceeding available stock | V.29 9k | 0.890 | PURCHASE_ORDER (0.97) | HUMAN_REVIEW | safe |
| `MFG-05` | 5 | Bilingual supplier PO, unknown part, no reply fax number | V.29 9k | 0.708 | PURCHASE_ORDER (0.91) | HUMAN_REVIEW | safe |
| `OFF-01` | 1 | Office supply reorder | V.34 33k | 0.974 | PURCHASE_ORDER (0.99) | AUTO_ACTION | safe |
| `OFF-02` | 2 | Vendor invoice and remittance advice | V.34 33k | 0.961 | INVOICE_REMITTANCE (0.94) | ROUTE | safe |
| `OFF-03` | 3 | Unsolicited advertising fax | V.17 14k | 0.963 | SPAM_OTHER (0.99) | ARCHIVE | safe |
| `OFF-04` | 4 | Executed service agreement signature page | V.29 9k | 0.760 | CONTRACT_DOCUMENT (0.76) | ROUTE | safe |
| `OFF-05` | 5 | Law firm employment-records request naming a real patient | V.17 14k | 0.975 | LEGAL_RECORDS_REQUEST (1.00) | ROUTE | safe |
| `MIL-01` | 1 | Routine MILSTRIP requisition, DD Form 1348-1A | V.34 33k | 0.973 | MILSTRIP_REQUISITION (1.00) | ROUTE | safe |
| `MIL-02` | 2 | Contract delivery order, DD Form 1155 with DFARS flow-downs | V.17 14k | 0.961 | CONTRACT_DOCUMENT (1.00) | ROUTE | safe |
| `MIL-03` | 3 | Priority 03 casualty requisition, stock exactly equal to demand | V.17 14k | 0.950 | MILSTRIP_REQUISITION (1.00) | ROUTE | safe |
| `MIL-04` | 4 | SECRET//NOFORN marked page delivered to an unclassified DID | V.17 14k | 0.959 | CLARIFICATION_NEEDED (0.56) | QUARANTINE | safe |
| `MIL-05` | 5 | Field-expedient requisition over a degraded tactical circuit | V.27ter 4k, 1pg lost, no ECM | 0.428 | CLARIFICATION_NEEDED (0.29) | HUMAN_REVIEW | safe |

## Transport observations

- 2 of 20 faxes lost at least one page in transit (MRO-05, MIL-05). In every case the audit log records a successful reception, because T.30 confirms the pages it received, not the pages that were sent. A recipient reading the log cannot tell that `MRO-05`'s parts list never arrived.
- 1 fax negotiated ECM off (MIL-05), so page errors became permanent scanline damage rather than retransmissions.
- The modulation ladder behaved as specified: V.34 on clean lines down to V.27ter at 4.8 kbps on the tactical circuit, where a 3-page fax took 108 seconds to transfer.
- Audit hash chains verified intact on 20/20 runs.

## Reproducing

```bash
cd protocol-box-sim
python3 run_simulation.py --json reports/results.json
python3 generate_report.py

python3 run_simulation.py --profile baseline --case OFF-05 -v   # audit log
python3 run_simulation.py --vertical Military --no-color
```

Runs are deterministic under a fixed `--seed` (default 20260314). Transport and OCR draw an identical random stream in both profiles.
