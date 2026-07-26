"""End-to-end run of one fax through the eight-stage pipeline (section 12.1)."""

import random

from .audit import AuditLogger
from .nlu import classify, extract_entities
from .ocr import run_ocr
from .spec import GO_LIVE_CRITERIA, SKU_PROFILES, STAGE_LATENCY
from .telephony import InboundFaxSession
from .workflow import WorkflowProcessor


def _lat(stage, rng, scale=1.0):
    lo, hi = STAGE_LATENCY[stage]
    return rng.uniform(lo, hi) * scale


def _norm(value):
    return " ".join(str(value).strip().lower().replace(".", "").split())


def _entity_match(etype, got, want):
    if got is None:
        return False
    g, w = _norm(got), _norm(want)
    if etype == "QUANTITY":
        gd = "".join(c for c in g if c.isdigit())
        wd = "".join(c for c in w if c.isdigit())
        return bool(wd) and gd == wd
    if etype == "FAX_NUMBER":
        gd = "".join(c for c in g if c.isdigit())[-10:]
        wd = "".join(c for c in w if c.isdigit())[-10:]
        return bool(wd) and gd == wd
    return g == w


def run_case(case, profile="baseline", seed=20260314):
    # The seed deliberately excludes the profile so transport and OCR draw the
    # identical random stream in both runs. Baseline and hardened therefore see
    # byte-identical OCR text, and every difference between them is attributable
    # to the pipeline change rather than to luck.
    rng = random.Random(f"{case.case_id}|{seed}")
    audit = AuditLogger(case.case_id, device_serial=f"{case.sku}-2026-001")
    sku = SKU_PROFILES[case.sku]

    # --- Stage 1: T.30 ingest ---------------------------------------------
    inbound = InboundFaxSession(case, rng, audit).receive()
    audit.advance(inbound["transfer_sec"])

    # Degradation multiplier applied to the compute stages: damaged pages cost
    # more in preprocessing and in Tesseract's LSTM beam search.
    sq = case.source_quality
    degradation = 1.0 + sq.get("noise", 0) * 1.8 + sq.get("thermal_fade", 0) * 1.2 \
        + min(abs(sq.get("skew_deg", 0)), 8.0) * 0.05

    ttfa = 0.0

    # --- Stage 2: detect ---------------------------------------------------
    d = _lat("detect", rng)
    ttfa += d
    audit.advance(d)
    audit.log("SPOOL_EVENT", watcher="inotify", latency_ms=round(d * 1000, 1))

    # --- Stages 3+4: preprocess and OCR ------------------------------------
    pages = max(1, inbound["pages_received"])
    pre = _lat("preprocess", rng) * degradation * (1 + 0.35 * (pages - 1))
    ttfa += pre
    audit.advance(pre)

    ocr = run_ocr(case, rng, audit)
    ocr_sec = (ocr["pages_ocrd"] / (sku["ocr_pages_per_min"] / 60.0)) * degradation
    ttfa += ocr_sec
    audit.advance(ocr_sec)

    # --- Stage 5: intent classification ------------------------------------
    c = _lat("classify", rng)
    ttfa += c
    audit.advance(c)
    intent_result = classify(ocr["text"], profile=profile)

    # --- Stage 6: entity extraction ----------------------------------------
    e = _lat("extract_entities", rng)
    ttfa += e
    audit.advance(e)
    entities = extract_entities(
        ocr["text"],
        confidences=_token_confs(case, ocr),
        profile=profile,
    )

    # --- Stage 7: execute --------------------------------------------------
    x = _lat("execute", rng)
    ttfa += x
    audit.advance(x)

    doc = {
        "intent": intent_result["intent"],
        "confidence": intent_result["confidence"],
        "entities": entities,
        "text": ocr["text"],
        "review_rule": intent_result.get("review_rule"),
    }
    wf = WorkflowProcessor(case, rng, audit, profile=profile)
    result = wf.process_document(doc)

    chain_ok, bad_row = audit.verify_chain()

    # --- scoring -----------------------------------------------------------
    expected_intent = case.expected_for(profile)
    intent_correct = intent_result["intent"] == expected_intent
    disposition_safe = result.disposition in case.safe_dispositions
    disposition_optimal = result.disposition == case.optimal_disposition

    ent_checks = {}
    for etype, want in case.required_entities.items():
        got = entities.get(etype, {}).get("value")
        ent_checks[etype] = {
            "expected": want, "got": got,
            "match": _entity_match(etype, got, want),
        }
    ent_total = len(ent_checks)
    ent_hits = sum(1 for v in ent_checks.values() if v["match"])
    ent_accuracy = (ent_hits / ent_total) if ent_total else None

    phi_released = bool(result.extra.get("phi_released"))
    phi_misdirection = phi_released and case.did_class != "clinical"

    spillage_expected = case.optimal_disposition == "QUARANTINE"
    spillage_unhandled = spillage_expected and result.disposition != "QUARANTINE"

    # A committed ERP transaction against a part the catalogue does not contain
    # is a phantom order: the customer gets an acknowledgment for goods that
    # cannot ship, and nothing in the pipeline raised an error.
    phantom_order = (
        result.disposition == "AUTO_ACTION"
        and "order_id" in result.extra
        and result.extra.get("part_found") is False
    )

    return {
        "case_id": case.case_id,
        "vertical": case.vertical,
        "difficulty": case.difficulty,
        "title": case.title,
        "sku": case.sku,
        "profile": profile,
        "transport": {
            "modulation": inbound["modulation"]["standard"],
            "bps": inbound["modulation"]["bps"],
            "ecm": inbound["ecm_active"],
            "transfer_sec": inbound["transfer_sec"],
            "pages_sent": inbound["pages_sent"],
            "pages_received": inbound["pages_received"],
            "pages_lost": inbound["pages_lost"],
            "uncorrected_page_errors": inbound["uncorrected_page_errors"],
            "tiff_sha256": inbound["tiff_sha256"][:16],
        },
        "ocr": {
            "avg_confidence": ocr["avg_confidence"],
            "char_error_rate": ocr["char_error_rate"],
            "low_confidence_tokens": ocr["low_confidence_tokens"],
            "token_count": ocr["token_count"],
            "psm": ocr["psm"],
            "below_threshold": ocr["avg_confidence"] < 0.60,
            "sample": ocr["low_confidence_sample"],
        },
        "nlu": {
            "intent": intent_result["intent"],
            "confidence": intent_result["confidence"],
            "original_intent": intent_result.get("original_intent"),
            "top_probabilities": intent_result["probabilities"],
            "review_rule": intent_result.get("review_rule"),
        },
        "entities": {k: v for k, v in entities.items()},
        "entity_checks": ent_checks,
        "workflow": result.as_dict(),
        "outbound": wf.outbound,
        "controls_fired": wf.controls_fired,
        "scoring": {
            "expected_intent": expected_intent,
            "intent_correct": intent_correct,
            "optimal_disposition": case.optimal_disposition,
            "disposition": result.disposition,
            "disposition_safe": disposition_safe,
            "disposition_optimal": disposition_optimal,
            "entity_accuracy": ent_accuracy,
            "phi_misdirection": phi_misdirection,
            "spillage_unhandled": spillage_unhandled,
            "phantom_order": phantom_order,
        },
        "timing": {
            "ttfa_sec": round(ttfa, 2),
            "ttfa_budget_sec": sku["ttfa_budget_sec"],
            "ttfa_within_budget": ttfa <= sku["ttfa_budget_sec"],
            "t30_transfer_sec": inbound["transfer_sec"],
            "wall_clock_sec": audit.clock,
        },
        "audit": {
            "entries": audit.entries,
            "rendered": audit.render(),
            "chain_valid": chain_ok,
            "chain_break_at": bad_row,
        },
        "hazard": case.hazard,
        "notes": case.notes,
    }


def _token_confs(case, ocr):
    """Rebuild (token, confidence) pairs from the OCR pass for entity scoring."""
    # run_ocr already computed these; recompute deterministically from the same
    # degradation characteristics so entity-level confidence tracks the document.
    base = ocr["avg_confidence"]
    pairs = []
    hw_tokens = set()
    for line in case.raw_text.split("\n"):
        if "[[hw]]" in line:
            seg = line.split("[[hw]]", 1)[1].split("[[/hw]]", 1)[0]
            hw_tokens.update(t.strip(".,:;#") for t in seg.split())
    for tok in ocr["text"].split():
        clean = tok.strip(".,:;#")
        conf = base
        if clean in hw_tokens or any(h[:4] and h[:4] in clean for h in hw_tokens if len(h) > 4):
            conf = max(0.05, base - 0.42)
        pairs.append((clean, round(min(0.99, max(0.05, conf)), 3)))
    return pairs


def score_run(results):
    """Aggregate against the section 16.3 Ghost Mode go-live criteria."""
    n = len(results)
    intent_ok = sum(1 for r in results if r["scoring"]["intent_correct"])
    safe = sum(1 for r in results if r["scoring"]["disposition_safe"])
    optimal = sum(1 for r in results if r["scoring"]["disposition_optimal"])
    ent_scores = [r["scoring"]["entity_accuracy"] for r in results
                  if r["scoring"]["entity_accuracy"] is not None]
    phi = sum(1 for r in results if r["scoring"]["phi_misdirection"])
    spill = sum(1 for r in results if r["scoring"]["spillage_unhandled"])
    phantom = sum(1 for r in results if r["scoring"]["phantom_order"])
    ocr_conf = sum(r["ocr"]["avg_confidence"] for r in results) / n
    ttfa_ok = sum(1 for r in results if r["timing"]["ttfa_within_budget"])

    metrics = {
        "sample_size": n,
        "intent_accuracy": intent_ok / n,
        "disposition_safe_rate": safe / n,
        "disposition_optimal_rate": optimal / n,
        "entity_accuracy": (sum(ent_scores) / len(ent_scores)) if ent_scores else 0.0,
        "phi_misdirection_count": phi,
        "phi_misdirection_rate": phi / n,
        "spillage_unhandled_count": spill,
        "phantom_order_count": phantom,
        "avg_ocr_confidence": ocr_conf,
        "ttfa_within_budget_rate": ttfa_ok / n,
        "avg_ttfa_sec": sum(r["timing"]["ttfa_sec"] for r in results) / n,
    }

    gate = {}
    for key, crit in GO_LIVE_CRITERIA.items():
        value = metrics.get(key)
        if value is None:
            continue
        if crit["op"] == ">=":
            passed = value >= crit["threshold"]
        else:
            passed = value == crit["threshold"]
        gate[key] = {
            "label": crit["label"], "threshold": crit["threshold"],
            "op": crit["op"], "value": value, "pass": passed,
        }
    metrics["go_live_gate"] = gate
    metrics["go_live_pass"] = all(g["pass"] for g in gate.values())
    return metrics
