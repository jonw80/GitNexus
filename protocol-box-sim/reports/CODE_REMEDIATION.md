# Protocol Box — Code Remediation Report

**Scope:** every source block in Master Internal Build File v4.1 — `preprocess.py`,
`classify.py`, `fhir_client.py`, `hl7_client.py`, `erp_rest_client.py`,
`processor.js`, `docker-compose.yml`, and the operational YAML in Appendix E.

**Method:** static audit of the shipped source, plus a 20-fax behavioural
simulation of the section 12–14 pipeline (`protocol-box-sim/`). Findings are
marked **[STATIC]** where they are provable by reading your code, and
**[SIM]** where they depend on the behavioural model. Static findings do not
rest on any assumption about your classifier.

**Bottom line:** 36 defects. The blocker is not accuracy tuning — it is that
five of the subsystems the document presents as complete cannot execute as
written. The dead-letter queue cannot insert a row. The retry engine it belongs
to does not exist. FHIR authentication is an empty function. The document
downloader calls a method that was never defined. And the container that talks
to every external system of record is attached to a network with no egress.

None of that is visible from the document's prose, which describes all five as
implemented.

---

## P1 — Cannot execute as written

These are not edge cases. Each one fails on the first call.

### 1.1 The dead-letter queue cannot insert a pending row **[STATIC]**

`hl7_client.py`, `MLLPDeadLetterQueue.enqueue()`:

```python
'NOW() + INTERVAL \'60 seconds\'' if initial_status == 'PENDING' else None,
```

This is passed as a **bound parameter** for the `next_retry_at` TIMESTAMP column.
Bound parameters are values, not SQL — the driver sends the literal 27-character
string `NOW() + INTERVAL '60 seconds'`, and PostgreSQL raises
`invalid input syntax for type timestamp`.

Every `enqueue()` for a `PENDING` message raises. The DLQ is the component the
document names as the mitigation for MLLP's primary failure mode — silent
message loss — and it cannot write a retryable row.

**Fix:** move the interval into the SQL text and bind only the delay, or compute
the timestamp in Python:

```python
next_retry = datetime.now(timezone.utc) + timedelta(
    seconds=policy.initial_delay_for(error_type)
) if initial_status == 'PENDING' else None
```

Note this also removes a second defect: the 60 seconds is hardcoded, so the
`initial_delay_seconds` and the per-error `error_overrides` in
`mllp_retry.yaml` (`CONNECTION_REFUSED: 120`, `APPLICATION_ERROR: 300`) are
ignored even when the insert is repaired.

### 1.2 The retry engine does not exist **[STATIC]**

Section 14.1.2.1 is titled *Dead-Letter Queue & Retry Engine*. The queue is
implemented. The retry engine is not.

`retry_pending()` returns locked rows and nothing consumes them. There is no
worker, no scheduler, no loop that re-sends a queued message. In consequence:

- `attempt_count` is hardcoded to `1` in the INSERT and never incremented
- `next_retry_at` is never advanced
- `backoff_multiplier`, `max_delay_seconds` and `max_attempts` have no consumer
- `terminal_conditions: max_attempts_exceeded` can never fire
- `terminal_conditions: message_age_exceeds_24h` is not implemented anywhere

A message that enters the DLQ stays there permanently. This is the same
outcome as the silent loss the section was written to prevent, with an audit
row attached.

**Fix:** implement the worker. It needs to claim a batch inside an explicit
transaction, re-send through `HL7Client`, increment `attempt_count`, apply
backoff from the policy, enforce `max_attempts`, and call
`mark_delivered`/`mark_abandoned`. Budget this as real work, not a patch — it
is the missing half of the subsystem.

### 1.3 `FOR UPDATE SKIP LOCKED` provides no protection as called **[STATIC]**

`retry_pending()` documents itself as preventing duplicate sends during HA
failover. Row locks only survive inside an open transaction. The method calls
`self.db.query(...)` and returns; unless that wrapper leaves an explicit
transaction open, the locks release the moment the function returns and two
workers can claim the same rows.

The docstring asserts *"No duplicates. No race conditions."* That guarantee is
not established by the code shown.

**Fix:** claim rows with an `UPDATE ... RETURNING` inside a transaction the
caller owns, or make the wrapper's transaction boundary explicit and tested.

### 1.4 FHIR authentication is a stub **[STATIC]**

`fhir_client.py`:

```python
def _authenticate(self, client_id, client_secret):
    '''OAuth 2.0 authentication with SMART on FHIR'''
    # Implementation depends on specific EMR
    pass
```

Section 14.1.1 states *"OAuth 2.0 with SMART on FHIR scopes. Credentials stored
in HashiCorp Vault."* No token is requested, no credential is read from Vault,
and no `Authorization` header is ever set on the FHIRClient session. Against a
correctly configured EMR every call returns 401.

**Fix:** implement the client-credentials or backend-services flow, cache and
refresh the token, and fail closed when acquisition fails. Until then no EMR
integration claim in the document is substantiated.

### 1.5 `_get_auth_headers()` is undefined **[STATIC]**

`download_document()` calls `self._get_auth_headers()`. No such method exists on
`FHIRClient`. Every document download raises `AttributeError`.

This is the function that retrieves the PHI the whole records-request workflow
exists to deliver.

### 1.6 `release_held_messages` uses a return value the driver does not provide **[STATIC]**

```python
released = self.db.execute('UPDATE ...', (cleared_dlq_id,))
if released > 0:
```

DB-API `execute()` returns `None` under psycopg2 and most wrappers; the row
count lives on `cursor.rowcount`. As written this raises
`TypeError: '>' not supported between instances of 'NoneType' and 'int'` —
inside the sequence-gate release path, which then never completes.

### 1.7 The integrations container has no network egress **[STATIC]**

`docker-compose.yml`:

```yaml
networks:
  pb-internal:
    driver: bridge
    internal: true
```

`pb-integrations` is attached to `pb-internal` only. An `internal: true` network
has no gateway to the outside. The container whose entire job is reaching FHIR
endpoints, ERP REST APIs and MLLP hosts cannot route to any of them.

**Fix:** give `pb-integrations` a second, egress-capable network with explicit
firewall rules, and keep `pb-internal` for inter-service traffic. This is the
right shape — the isolation instinct is correct, the wiring is not.

### 1.8 Vault is unreachable and the database has no credentials **[STATIC]**

- `pb-integrations` sets `VAULT_ADDR=http://localhost:8200`. Inside a container
  `localhost` is that container. Vault is not there.
- `pb-workflow` sets `DB_URL=postgresql://pb-storage:5432/protocolbox` with no
  user and no password, and is not granted the `db_password` secret, while
  `pb-storage` requires `POSTGRES_PASSWORD_FILE`. The workflow engine cannot
  authenticate to its own database.

### 1.9 The deskew step operates on the wrong pixel set **[STATIC]**

`preprocess.py`:

```python
img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
coords = np.column_stack(np.where(img > 0))
angle = cv2.minAreaRect(coords)[-1]
```

On a grayscale scan the background is near 255 and the text is near 0, so
`img > 0` selects essentially the entire page. `minAreaRect` therefore returns
the bounding box of the sheet, not of the text, and the angle is meaningless.
The canonical form of this snippet runs on an **inverted, binarized** image
where the text pixels are the non-zero ones.

Two related defects in the same block:

- The comment says *"Deskew using Hough transform."* The code uses
  `minAreaRect`. Neither is wrong as a technique; the documentation does not
  describe the implementation.
- The `if angle < -45: angle = -(90 + angle)` branch is written for OpenCV's
  pre-4.5 `minAreaRect` convention of `[-90, 0)`. Your target platform is
  Ubuntu 22.04, which ships OpenCV 4.5.4, where the range is `[0, 90)`. That
  branch is dead and the `else` branch rotates by the wrong angle.

**Fix:** binarize and invert before measuring, and normalise the angle
explicitly rather than relying on a version-dependent convention.

### 1.10 Cubic interpolation is applied to a binary image **[STATIC]**

The pipeline order is `adaptiveThreshold` → `cv2.resize(..., INTER_CUBIC)`.
Cubic interpolation of a two-valued image reintroduces intermediate grey values
and soft edges, which is precisely what Tesseract's LSTM does worst on.

**Fix:** resize before binarizing, or use `INTER_NEAREST` after. This is a
one-line change with measurable OCR accuracy impact.

---

## P2 — Executes, produces wrong results

### 2.1 Unknown parts pass the inventory guard **[STATIC]**

`processor.js`:

```js
const inventory = await this.erp.checkInventory(entities.PART_NUMBER);
if (inventory.available < entities.QUANTITY) { ... }
```

When the ERP has no record, `available` is `undefined`, and `undefined < n` is
`false` in JavaScript. The guard passes and a sales order is created against a
part that does not exist. In simulation this produced 4 phantom orders in 20
faxes; a single character of OCR damage to a part number is enough to trigger
it. **[SIM for the rate, STATIC for the defect.]**

If instead your unshown JS ERP client throws on 404, the outcome is different
but no better: the `catch` in `processDocument` logs `PROCESS_ERROR` and
**rethrows**, with nothing shown above to handle it. The sender receives no
reply at all.

**Fix:** `if (inventory.available === undefined || inventory.available < qty)`,
and give `processDocument` a terminal handler that always produces a
disposition.

### 2.2 `handleRecordsRequest` reads entities that do not exist **[STATIC]**

```js
const documents = await this.fhir.getDocuments(
    patient.id, entities.DOCUMENT_TYPE, entities.DOCUMENT_COUNT || 3
);
```

Section 13.4 defines eight entity types: `PATIENT_NAME`, `DATE_OF_BIRTH`,
`MRN`, `PART_NUMBER`, `QUANTITY`, `PO_NUMBER`, `FAX_NUMBER`, `FACILITY_NAME`.
`DOCUMENT_TYPE` and `DOCUMENT_COUNT` are not among them and no extractor
produces them. Both are permanently `undefined`.

The system therefore returns **three arbitrary documents for every records
request**, regardless of what was asked for. A request for "last 3 progress
notes and discharge summary" returns whatever the EMR lists first. That is both
a correctness failure and an over-disclosure risk — the requester receives PHI
they did not request and may not be authorised to hold.

### 2.3 Patient matching takes the first hit with no uniqueness check **[STATIC]**

`fhir_client.py`:

```python
results = search.perform_resources(self.client.server)
return results[0] if results else None
```

There is no check that the match is unique, no minimum-criteria rule, and no
disambiguation. A search on a common name returns an arbitrary patient.
`processor.js` passes whatever the NER produced, and the NER produces a
`PATIENT_NAME` from a regex.

Section 16.3 sets false-positive PHI misdirection at **0%**. This line makes
that target structurally unachievable: the code has no mechanism that could
distinguish a correct match from a wrong one.

**Fix:** require at least two corroborating identifiers, reject on multiple
matches rather than picking one, and log the candidate count for audit. This
is the single highest-value change in the report for a health or VA deployment.

### 2.4 Sequence gating has a check-then-insert race **[STATIC]**

`_check_sequence_gate()` runs a `SELECT`, then `enqueue()` runs an `INSERT`,
with no lock between them. Two concurrent failures for the same patient both
observe no blocker and both insert as `PENDING`. The gate fails silently under
exactly the concurrency it was built for.

**Fix:** advisory lock on `patient_mrn`, or a partial unique index that permits
only one `PENDING`/`RETRYING` row per patient.

### 2.5 The gate releases all held messages simultaneously **[STATIC]**

`mllp_retry.yaml` states *"Release held messages in FIFO order on upstream
clear."* `release_held_messages()` sets every held row to `PENDING` with
`next_retry_at = NOW()`. They then race through `retry_pending()`, which uses
`SKIP LOCKED` across concurrent workers.

For HL7 this is a clinical-safety issue, not a tidiness one: an `ADT^A08`
update overtaking the `ADT^A04` admit it amends corrupts the patient record.

**Fix:** release one message at a time, or carry an explicit sequence number
and have the worker refuse to send out of order.

### 2.6 A missing MRN argument permanently stalls a patient's queue **[STATIC]**

```python
def mark_delivered(self, dlq_id, patient_mrn=None):
    ...
    self.release_held_messages(dlq_id, patient_mrn)
```

and `release_held_messages` opens with `if not patient_mrn: return 0`.

The signature invites `mark_delivered(dlq_id)`. Called that way, held messages
for that patient are **never released** — a silent, permanent per-patient
deadlock with no alert.

**Fix:** read `patient_mrn` from the DLQ row rather than accepting it as an
optional argument.

### 2.7 PID-3 repetitions are not handled **[STATIC]**

```python
mrn_field = fields[3]
return mrn_field.split('^')[0] if mrn_field else None
```

PID-3 is a repeating field. Real EMRs commonly send
`123456^^^MRN~987-65-4321^^^SSN`. The code never splits on `~` and never checks
the assigning authority in PID-3.4, so it can return an SSN as the MRN — which
then becomes the sequence-gate key and lands in the `patient_mrn` column.

**Fix:** split on `~`, select the repetition whose PID-3.4 identifies the MRN
authority, and store nothing if no MRN-typed identifier is present.

### 2.8 Every retry would create a duplicate DLQ row **[STATIC]**

`enqueue()` always generates a fresh `dlq_id` and inserts `attempt_count = 1`.
There is no upsert on an existing entry. Once the missing retry worker (1.2)
exists, repeated failures will accumulate one row per attempt.

### 2.9 The ACK read has no overall deadline **[STATIC]**

```python
while True:
    chunk = sock.recv(4096)
```

`settimeout()` applies per `recv()`, not to the loop. A peer trickling one byte
every 29 seconds holds the worker indefinitely, which is the same worker-freeze
the surrounding comment claims the keepalive tuning prevents.

**Fix:** compute a deadline before the loop and check it each iteration.

### 2.10 Document download has no status check **[STATIC]**

`requests.get(attachment.url, ...)` with no `raise_for_status()`. A 401 or 404
returns the error body, which is then treated as document content, merged into
the reply PDF and faxed to the requester.

### 2.11 Reply destination is never validated **[STATIC]**

`faxSender.send({ destination: entities.FAX_NUMBER, ... })` with no null check,
on both the order path and the PHI path. An undefined destination is an
uncontrolled runtime failure rather than a routing decision. **[SIM]** In
simulation three of twenty runs had no extractable fax number, one of them the
records-request case.

### 2.12 Hardcoded 200 DPI assumption **[STATIC]**

`scale_factor = 300 / 200` with the comment *"Assume 200 DPI input."* ITU-T
standard mode is 204×98 and fine mode 204×196. A standard-mode fax is upscaled
by the wrong factor on the vertical axis, and the aspect ratio is never
corrected.

**Fix:** read the DPI from the TIFF tags and scale per axis.

---

## P3 — Claimed controls that are absent

Each of these is a statement made in the document that the code does not
implement. For a funding submission these are the most dangerous category,
because a technical reviewer who reads both will find the gap.

| # | Claim | Location | Reality |
|---|---|---|---|
| 3.1 | "TLS 1.3 for all external traffic" | §18, §21 STRIDE | `hl7_client.py` opens a plain `socket.AF_INET` TCP connection. PHI traverses MLLP in cleartext. No stunnel config appears anywhere in the document. |
| 3.2 | "Non-root containers" as the elevation-of-privilege mitigation | §21 STRIDE | `pb-telephony` runs `privileged: true` with `/dev:/dev` mounted. |
| 3.3 | "< 50ms on RK3588 NPU" | §13.1 | `pb-nlp` sets `DEVICE=cpu` and receives no `/dev/rknpu0` mapping. Only `pb-ocr` gets the NPU. |
| 3.4 | Authorization before EMR access | implied throughout §14 | No authorization, requester validation, or clinical-provenance check exists between classification and `findPatient`. |
| 3.5 | Classification handling for defence deployments | §6.2, §23 | No classification-banner detection anywhere in §12–14 or Appendix E. A marked page is OCR'd to the shared volume like any other. |
| 3.6 | `max_held_per_key: 50` | `mllp_retry.yaml` | Never read by any code. |
| 3.7 | `message_age_exceeds_24h` terminal condition | `mllp_retry.yaml` | Never implemented. |
| 3.8 | "Complete source code… enables complete system reconstruction" | §Purpose | Five subsystems in P1 cannot execute. The retry worker is absent. `processor.js` calls five methods never defined on the class — `generateCoverSheet`, `mergePdfs`, `routeToHumanReview`, `archiveOnly`, `createErrorResponse` — and imports four modules never shown: `./integrations/fhir`, `./integrations/erp`, `./fax/sender`, `./audit/logger`. Two of those duplicate the Python clients that *are* shown, so there are two unreconciled implementations of the FHIR and ERP paths. |

---

## P4 — Design and specification defects

### 4.1 Three intent classes are unreachable **[STATIC]**

Section 13.2 assigns actions to `LAB_RESULT` (provider inbox),
`PRESCRIPTION_REFILL` (pharmacy queue) and `INSURANCE_DENIAL` (billing). The
`switch` in section 14.3 has cases for `RECORDS_REQUEST`, `PURCHASE_ORDER`,
`CLARIFICATION_NEEDED` and `SPAM_OTHER` only. All three fall through to
`default: routeToHumanReview`. Three of your seven shipped classes cannot reach
their documented destination, and a perfect classifier cannot fix it.

### 4.2 `CLARIFICATION_NEEDED` is trained as a class **[STATIC]**

It appears in `self.labels` in `classify.py`, so the head can predict it — and
section 13.2 defines it as *"low confidence score."* A label whose definition is
a property of the output distribution cannot be a training target. The model can
emit `CLARIFICATION_NEEDED` at 0.95 confidence, which is incoherent.

**Fix:** six trained classes; `CLARIFICATION_NEEDED` becomes a routing decision
derived from the threshold, never a logit.

### 4.3 The taxonomy has no non-clinical classes **[STATIC for the gap, SIM for the impact]**

Seven classes, five clinical. Eight entity types, four clinical. There is no
class for an RFQ, a change order, an invoice, a work order, a MILSTRIP
requisition or a contract delivery order, and no entity type for NSN, CAGE
code, DODAAC or CLIN.

A softmax cannot abstain from a class it does not have. Faced with an industrial
or defence document the model must emit a wrong label; the only question is
whether it lands above or below threshold. **[SIM]** In simulation the military
vertical was the worst served, and the failures clustered in *clean* faxes
rather than degraded ones — high classifier confidence on documents the label
set cannot represent.

For an Army-facing product this is the gap that matters most. A DD Form 1155
delivery order auto-acknowledged as an ordinary sales order constitutes
acceptance of the DFARS clauses it incorporates.

### 4.4 The entity model is scalar **[STATIC]**

`handlePurchaseOrder` reads `entities.PART_NUMBER` and `entities.QUANTITY`,
singular. A multi-line purchase order has no representation, so lines beyond the
first are discarded with no error and no audit entry, while the acknowledgment
tells the customer the whole order was accepted. Multi-line and blanket orders
are the normal form of industrial procurement, not an edge case.

### 4.5 The audit trail does not reconcile sent against received **[STATIC]**

Section 22.2 hashes the TIFF on arrival and section 22 frames the chain as
evidence of *"integrity of the original."* T.30 confirms the pages that arrived,
not the pages that were sent, and no page-count reconciliation exists. **[SIM]**
Two faxes in the run lost a page and both logged a clean reception with a valid
seal. The legal-admissibility argument in section 22 claims more than the
mechanism delivers.

### 4.6 Documentation defects **[STATIC]**

- Section 20, *Compliance Certifications*, is listed in the table of contents
  and has **no content**.
- The YAML blocks at `mllp_retry.yaml` (`error_overrides`, `terminal_conditions`,
  `sequence_gating`, `alerting`) are collapsed onto single lines with escaped
  `\#` and `\-`. As printed they are not parseable YAML, which undermines the
  rebuild-from-scratch claim.
- Cover page and footer say *Version 4.0*; Document Control says *4.1.0*. Cover
  says *February 2026*; Document Control says *March 2026*.
- Section 12.1 gives classification latency as `< 500 ms`; section 13.1 gives
  `< 50ms`. Not contradictory, but a reviewer will ask.

---

## Suggested sequencing

The dependency order matters more than the severity order — several P2 fixes
are untestable until the P1 items land.

**Stage 1 — make it run.** 1.1, 1.4, 1.5, 1.6, 1.7, 1.8. Nothing downstream can
be validated until the DLQ inserts, FHIR authenticates, and the integrations
container can reach a network. Mostly small diffs; 1.7 needs a compose redesign.

**Stage 2 — build the missing half.** 1.2 and 1.3, the retry worker and its
transaction boundary. This is genuine engineering, not a patch.

**Stage 3 — stop wrong actions.** 2.1, 2.2, 2.3, 2.11. 2.3 is the one to do
first if you are pitching anything health- or VA-adjacent.

**Stage 4 — correctness under load.** 2.4 through 2.10.

**Stage 5 — image pipeline.** 1.9, 1.10, 2.12. Independent of everything above
and directly improves the OCR accuracy figures you quote.

**Stage 6 — model and taxonomy.** 4.1, 4.2, 4.3, 4.4. The largest scope. 4.3
requires new labelled data, which is also what section 16.3's ≥100-fax
criterion demands and which the document does not show evidence of holding.

**Stage 7 — close the claim gaps.** All of P3, plus 4.5 and 4.6. These are
credibility items: every one is a place where the document asserts something
the code does not do.

---

## What this report does not cover

**Test evidence.** Section 16.3 defines a go-live gate requiring ≥100 faxes with
≥95% intent accuracy, ≥90% entity accuracy, 0% PHI misdirection and ≥85% OCR
confidence. The document presents no measured results against it. A technical
reviewer will ask for that data, and the simulation in this repository is not a
substitute — it measures a stand-in classifier against synthetic documents.
Collecting a real labelled corpus is prerequisite work for both the gate and
for fixing 4.3.

**Compliance and procurement.** Certification posture, ATO path, supply-chain
provenance of the compute module, and the specific requirements of whichever
solicitation you are answering are out of scope here and should be assessed
separately with your contracting contact. The RMF mapping in section 24 covers
19 controls across 7 families, one of them marked N/A; the NIST SP 800-53 Rev. 5
moderate baseline is substantially larger and spans 20 families, and section 20
is empty.

**Hardware.** The netlists, FXO carrier design and thermal analysis were not
audited.
