# Protocol Box — Simulation Fax Harness

A runnable simulation of the Protocol Box v4.1 inbound fax pipeline, built to
answer one question: **what happens when documents that are not healthcare
records arrive at an appliance whose intent model was trained on healthcare
records?**

The harness implements the eight-stage pipeline from section 12.1 of the Master
Internal Build File and drives 20 synthetic faxes through it — four verticals
(MRO, manufacturer ordering, office, military) at five difficulty tiers each.

Results and findings: [`reports/SIMULATION_REPORT.md`](reports/SIMULATION_REPORT.md).

## Running it

No dependencies beyond Python 3.8+.

```bash
python3 run_simulation.py                            # both profiles, full corpus
python3 run_simulation.py --json reports/results.json
python3 generate_report.py                           # renders the markdown report

python3 run_simulation.py --profile baseline         # v4.1 exactly as specified
python3 run_simulation.py --vertical Military
python3 run_simulation.py --difficulty 4 --difficulty 5
python3 run_simulation.py --case OFF-05 -v           # one case with its audit log
```

Runs are deterministic under a fixed `--seed` (default `20260314`).

## The two profiles

`baseline` is the pipeline as the build file specifies it: the seven intent
classes of section 13.2, the eight entity types of section 13.4, the 0.60
confidence threshold of section 12.3, and the `switch` statement of section 14.3
ported without modification — including its bugs.

`hardened` adds six proposed controls. Each is gated behind a single flag so the
baseline path stays byte-identical:

| ID | Control |
|---|---|
| `PB-C1` | Classification banner detector, runs before OCR export |
| `PB-C2` | Extended intent taxonomy (7 additional classes) |
| `PB-C3` | PHI scope guard on the EMR path |
| `PB-C4` | Per-entity confidence floor on order-critical fields |
| `PB-C5` | Reply-path guard for PHI payloads |
| `PB-C6` | Explicit unknown-part check before order creation |

Both profiles draw the **same random stream** for transport and OCR, so a case
sees byte-identical OCR text in both runs. Every difference between the two
columns is attributable to the pipeline change rather than to sampling.

## What is actually simulated

| Stage | Module | Models |
|---|---|---|
| 1. Ingest | `pbsim/telephony.py` | T.30 phases A–E, V.34/V.17/V.29/V.27ter modulation ladder driven by line quality, ECM negotiation, page loss, SHA-256 digital seal |
| 2. Detect | `pbsim/engine.py` | inotify spool event |
| 3. Preprocess | `pbsim/ocr.py` | deskew / denoise / adaptive threshold / DPI normalisation, each contributing a recovery multiplier |
| 4. Extract | `pbsim/ocr.py` | character-level degradation with a Tesseract confusion table, per-token confidence, handwriting at ~6.5× the machine-print error rate |
| 5. Classify | `pbsim/nlu.py` | weighted lexical evidence model with temperature-scaled softmax, 0.60 threshold → `CLARIFICATION_NEEDED` |
| 6. NER | `pbsim/nlu.py` | label-anchored patterns for the section 13.4 entity types |
| 7. Execute | `pbsim/workflow.py` | port of `processor.js`, against mock FHIR R4 and REST ERP backends |
| 8. Respond | `pbsim/telephony.py` | outbound status state machine, E001–E007 error codes, section 17.4 retry ladder with jitter |

Throughout: an append-only audit log with per-row hash chaining, matching the
chain-of-evidence model in section 22.

### The intent model

`pbsim/nlu.py` stands in for the fine-tuned DistilBERT head with a weighted
lexical evidence model. Its vocabulary coverage deliberately mirrors the
training distribution the build file describes — *"50,000 labeled fax samples
(healthcare + manufacturing)"* — so it is dense on clinical and purchase-order
language and thin on MRO, office-administrative and defence-logistics
vocabulary. That asymmetry is the point of the experiment, not an artifact of
it.

This is not a claim about what the real model would score. It is a claim about
what a model trained on that distribution has no way to represent, which is a
property of the taxonomy in section 13.2 rather than of any particular set of
weights.

## Corpus

`pbsim/corpus.py`. Difficulty is a composite of transport quality, document
structure, and semantic distance from the training distribution:

- **D1** clean transport, in-taxonomy intent, single action
- **D2** clean transport, in-taxonomy intent, branch logic (inventory, urgency)
- **D3** clean transport, intent outside the shipped taxonomy
- **D4** degraded transport or handwriting, plus taxonomy or safety pressure
- **D5** compound: degraded transport *and* structure *and* taxonomy

Two cases carry deliberate safety hazards: `OFF-05` is a law-firm request for
employment records naming someone who is also a patient in the EMR, and `MIL-04`
is a SECRET//NOFORN page misdialled onto a commercial DID.

Every fax in the corpus is synthetic. Names, part numbers, NSNs, DODAACs, CAGE
codes, contract numbers and fax numbers are fabricated.

## Scoring

Each case declares an expected intent, an optimal disposition, and a set of
dispositions that are *safe* (not harmful) even if not optimal. Aggregate
metrics are checked against the section 16.3 Ghost Mode go-live criteria.

Four harm classes are counted separately from accuracy, because a system can be
accurate on average and still commit them:

- **PHI misdirection** — protected records released to an unauthorised requester
- **Uncontained spillage** — marked classified material processed on an
  unclassified appliance
- **Phantom order** — an ERP transaction committed against a part number the
  catalogue does not contain
- **TTFA breach** — time to first action exceeding the SKU budget

## Layout

```
pbsim/spec.py        constants transcribed from the build file, each with a section citation
pbsim/telephony.py   T.30 inbound, outbound job state machine, retry ladder
pbsim/ocr.py         preprocessing and character-level degradation
pbsim/nlu.py         intent classification and entity extraction
pbsim/workflow.py    processor.js port plus the proposed controls
pbsim/backends.py    mock FHIR R4 and REST ERP
pbsim/audit.py       hash-chained append-only audit log
pbsim/corpus.py      the 20 fax cases
pbsim/engine.py      per-case orchestration and scoring
run_simulation.py    CLI
generate_report.py   renders reports/SIMULATION_REPORT.md from results.json
```
