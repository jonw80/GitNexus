#!/usr/bin/env python3
"""Drive the Protocol Box simulation fax corpus through the v4.1 pipeline.

  python3 run_simulation.py                      # both profiles, full corpus
  python3 run_simulation.py --profile baseline   # v4.1 as specified
  python3 run_simulation.py --vertical Military  # one vertical
  python3 run_simulation.py --case MIL-04 -v     # one case with the audit log
"""

import argparse
import json
import os
import sys

from pbsim.corpus import CASES, VERTICALS
from pbsim.engine import run_case, score_run

HERE = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(HERE, "reports")

GREEN, RED, YELLOW, DIM, BOLD, RESET = (
    "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[1m", "\033[0m"
)


def _c(text, color, enabled):
    return f"{color}{text}{RESET}" if enabled else text


def print_case(r, color, verbose=False):
    s = r["scoring"]
    t = r["transport"]
    mark = _c("PASS", GREEN, color) if s["disposition_safe"] else _c("FAIL", RED, color)
    if s["phi_misdirection"] or s["spillage_unhandled"]:
        mark = _c("BREACH", RED, color)

    print(f"\n{_c(r['case_id'], BOLD, color)}  D{r['difficulty']}  {r['title']}")
    print(f"  {_c('transport', DIM, color)}   {t['modulation']} @ {t['bps']}bps  "
          f"ECM={'on' if t['ecm'] else 'off'}  "
          f"pages {t['pages_received']}/{t['pages_sent']}"
          + (f"  {_c('LOST ' + str(t['pages_lost']), RED, color)}" if t["pages_lost"] else "")
          + (f"  {_c(str(t['uncorrected_page_errors']) + ' uncorrected', YELLOW, color)}"
             if t["uncorrected_page_errors"] else ""))
    ocr = r["ocr"]
    conf_txt = f"{ocr['avg_confidence']:.3f}"
    if ocr["below_threshold"]:
        conf_txt = _c(conf_txt + " (below 0.60 floor)", RED, color)
    elif ocr["avg_confidence"] < 0.85:
        conf_txt = _c(conf_txt + " (below 0.85 go-live bar)", YELLOW, color)
    print(f"  {_c('ocr', DIM, color)}         conf {conf_txt}  CER {ocr['char_error_rate']:.3f}  "
          f"PSM {ocr['psm']}  {ocr['low_confidence_tokens']}/{ocr['token_count']} weak tokens")

    n = r["nlu"]
    itxt = f"{n['intent']} @ {n['confidence']:.3f}"
    itxt = _c(itxt, GREEN if s["intent_correct"] else RED, color)
    exp = "" if s["intent_correct"] else _c(f"  expected {s['expected_intent']}", DIM, color)
    print(f"  {_c('intent', DIM, color)}      {itxt}{exp}")
    if n.get("original_intent"):
        print(f"              {_c('pre-threshold argmax: ' + n['original_intent'], DIM, color)}")

    if r["entity_checks"]:
        parts = []
        for et, chk in r["entity_checks"].items():
            ok = "ok" if chk["match"] else "MISS"
            got = chk["got"] if chk["got"] is not None else "-"
            parts.append(_c(f"{et}={got} [{ok}]", GREEN if chk["match"] else RED, color))
        print(f"  {_c('entities', DIM, color)}    " + "  ".join(parts))

    w = r["workflow"]
    dtxt = _c(w["disposition"], GREEN if s["disposition_safe"] else RED, color)
    print(f"  {_c('disposition', DIM, color)} {dtxt}  {_c('->', DIM, color)} {w['action']}")
    if r["controls_fired"]:
        print(f"  {_c('controls', DIM, color)}    " + ", ".join(r["controls_fired"]))
    for job in r["outbound"]:
        status = job["status"]
        line = f"{job['job_id']} {status} after {job['attempts']} attempt(s)"
        if status == "failed":
            line += f" [{job.get('error_code')}]"
        print(f"  {_c('outbound', DIM, color)}    "
              + _c(line, GREEN if status == "completed" else RED, color))

    tm = r["timing"]
    ttxt = f"{tm['ttfa_sec']:.1f}s / {tm['ttfa_budget_sec']:.0f}s budget"
    ttxt = _c(ttxt, GREEN if tm["ttfa_within_budget"] else RED, color)
    print(f"  {_c('ttfa', DIM, color)}        {ttxt}   "
          f"{_c('T.30 transfer ' + str(tm['t30_transfer_sec']) + 's', DIM, color)}")

    if s["phi_misdirection"]:
        print(_c("  *** PHI MISDIRECTION: protected records released to an "
                 "unauthorised requester ***", RED, color))
    if s["spillage_unhandled"]:
        print(_c("  *** CLASSIFIED SPILLAGE NOT CONTAINED: marked material "
                 "processed on an unclassified appliance ***", RED, color))
    if s["phantom_order"]:
        print(_c("  *** PHANTOM ORDER: sales order committed against a part "
                 "number the ERP catalogue does not contain ***", RED, color))

    if verbose:
        print(_c("  --- audit log ---", DIM, color))
        for line in r["audit"]["rendered"].split("\n"):
            print("  " + _c(line, DIM, color))
        print(f"  {_c('hash chain valid: ' + str(r['audit']['chain_valid']), DIM, color)}")


def print_summary(profile, results, metrics, color):
    print(f"\n{_c('=' * 78, DIM, color)}")
    print(_c(f"PROFILE: {profile.upper()}  -  {len(results)} faxes", BOLD, color))
    print(_c("=" * 78, DIM, color))

    print(f"\n{_c('Per-vertical', BOLD, color)}")
    print(f"  {'vertical':<24} {'safe':>7} {'optimal':>9} {'intent':>8} {'ocr':>7} {'ttfa':>8}")
    for v in VERTICALS:
        rs = [r for r in results if r["vertical"] == v]
        if not rs:
            continue
        safe = sum(1 for r in rs if r["scoring"]["disposition_safe"])
        opt = sum(1 for r in rs if r["scoring"]["disposition_optimal"])
        it = sum(1 for r in rs if r["scoring"]["intent_correct"])
        oc = sum(r["ocr"]["avg_confidence"] for r in rs) / len(rs)
        tt = sum(r["timing"]["ttfa_sec"] for r in rs) / len(rs)
        line = (f"  {v:<24} {safe}/{len(rs):>5} {opt}/{len(rs):>7} "
                f"{it}/{len(rs):>6} {oc:>7.3f} {tt:>7.1f}s")
        print(_c(line, GREEN if safe == len(rs) else RED, color))

    print(f"\n{_c('By difficulty', BOLD, color)}")
    print(f"  {'tier':<6} {'safe':>7} {'optimal':>9} {'intent':>8} {'ocr':>7}")
    for d in sorted({r["difficulty"] for r in results}):
        rs = [r for r in results if r["difficulty"] == d]
        safe = sum(1 for r in rs if r["scoring"]["disposition_safe"])
        opt = sum(1 for r in rs if r["scoring"]["disposition_optimal"])
        it = sum(1 for r in rs if r["scoring"]["intent_correct"])
        oc = sum(r["ocr"]["avg_confidence"] for r in rs) / len(rs)
        line = f"  D{d:<5} {safe}/{len(rs):>5} {opt}/{len(rs):>7} {it}/{len(rs):>6} {oc:>7.3f}"
        print(_c(line, GREEN if safe == len(rs) else RED, color))

    print(f"\n{_c('Section 16.3 Ghost Mode go-live gate', BOLD, color)}")
    for key, g in metrics["go_live_gate"].items():
        val = g["value"]
        vtxt = f"{val:.3f}" if isinstance(val, float) else str(val)
        status = _c("PASS", GREEN, color) if g["pass"] else _c("FAIL", RED, color)
        print(f"  {status}  {g['label']:<42} {vtxt:>8}  (need {g['op']} {g['threshold']})")
    verdict = ("CLEARED FOR AUTO-REPLY" if metrics["go_live_pass"]
               else "BLOCKED - REMAIN IN GHOST MODE")
    print("\n  " + _c(verdict, GREEN if metrics["go_live_pass"] else RED, color))

    print(f"\n{_c('Additional metrics', BOLD, color)}")
    print(f"  safe disposition rate       {metrics['disposition_safe_rate']:.3f}")
    print(f"  optimal disposition rate    {metrics['disposition_optimal_rate']:.3f}")
    print(f"  PHI misdirection events     {metrics['phi_misdirection_count']}")
    print(f"  uncontained spillage events {metrics['spillage_unhandled_count']}")
    print(f"  phantom ERP orders          {metrics['phantom_order_count']}")
    print(f"  TTFA within SKU budget      {metrics['ttfa_within_budget_rate']:.3f}")
    print(f"  mean TTFA                   {metrics['avg_ttfa_sec']:.1f}s")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", choices=["baseline", "hardened", "both"], default="both")
    ap.add_argument("--vertical", action="append", choices=VERTICALS)
    ap.add_argument("--difficulty", action="append", type=int, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--case", action="append")
    ap.add_argument("--seed", type=int, default=20260314)
    ap.add_argument("-v", "--verbose", action="store_true", help="print audit logs")
    ap.add_argument("--json", metavar="PATH", help="write full results as JSON")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    color = not args.no_color and sys.stdout.isatty()

    cases = CASES
    if args.vertical:
        cases = [c for c in cases if c.vertical in args.vertical]
    if args.difficulty:
        cases = [c for c in cases if c.difficulty in args.difficulty]
    if args.case:
        wanted = {c.upper() for c in args.case}
        cases = [c for c in cases if c.case_id.upper() in wanted]
    if not cases:
        print("no cases matched", file=sys.stderr)
        return 2

    profiles = ["baseline", "hardened"] if args.profile == "both" else [args.profile]
    all_out = {}

    for profile in profiles:
        print(f"\n{_c('#' * 78, DIM, color)}")
        print(_c(f"# PROTOCOL BOX v4.1 SIMULATION FAX RUN - profile: {profile}", BOLD, color))
        print(_c(f"# {len(cases)} faxes | seed {args.seed}", DIM, color))
        print(_c("#" * 78, DIM, color))

        results = [run_case(c, profile=profile, seed=args.seed) for c in cases]
        for r in results:
            print_case(r, color, verbose=args.verbose)
        metrics = score_run(results)
        print_summary(profile, results, metrics, color)
        all_out[profile] = {"metrics": metrics, "results": results}

    if len(profiles) == 2:
        b, h = all_out["baseline"]["metrics"], all_out["hardened"]["metrics"]
        print(f"\n{_c('=' * 78, DIM, color)}")
        print(_c("BASELINE (v4.1 as specified)  vs  HARDENED (proposed controls)", BOLD, color))
        print(_c("=" * 78, DIM, color))
        rows = [
            ("intent accuracy", "intent_accuracy", "{:.3f}"),
            ("safe disposition rate", "disposition_safe_rate", "{:.3f}"),
            ("optimal disposition rate", "disposition_optimal_rate", "{:.3f}"),
            ("entity accuracy", "entity_accuracy", "{:.3f}"),
            ("PHI misdirection events", "phi_misdirection_count", "{}"),
            ("uncontained spillage events", "spillage_unhandled_count", "{}"),
            ("phantom ERP orders", "phantom_order_count", "{}"),
        ]
        print(f"  {'metric':<30} {'baseline':>10} {'hardened':>10}   delta")
        for label, key, fmt in rows:
            bv, hv = b[key], h[key]
            delta = hv - bv
            arrow = "improved" if (delta > 0 if "count" not in key else delta < 0) else \
                    ("same" if delta == 0 else "worse")
            print(f"  {label:<30} {fmt.format(bv):>10} {fmt.format(hv):>10}   "
                  + _c(arrow, GREEN if arrow == "improved" else DIM, color))

    if args.json:
        path = args.json
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        with open(path, "w") as fh:
            json.dump(all_out, fh, indent=2, default=str)
        print(f"\nwrote {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
