#!/usr/bin/env python3
"""
check_ledger.py  --  consistency check of the UGCT derivation ledger.

Usage:
  python3 check_ledger.py derivation_ledger.json
  python3 check_ledger.py derivation_ledger.json --lean report.txt

Without --lean it checks that the labels are logically consistent and reports what every
claim rests on.  It does not check mathematics: 'kind' and 'basis' come from the audits.

With --lean it also reads the output of `lake env lean Report.lean` (Lean's `#print axioms`
for each theorem) and checks every node that names Lean theorems against what the kernel
reports.  For those nodes the dependency on postulates and conjectures is computed by Lean,
not typed by hand.

Rules (exit code 1 if any is broken):
  R0  ids unique, every dependency exists, no cycles
  R1  a PROVEN node depends only on PROVEN or IMPORT nodes
  R1b a CONDITIONAL node depends only on PROVEN, IMPORT, CONJECTURE or CONDITIONAL nodes,
      and on at least one CONJECTURE
  R2  an IMPORT or CONJECTURE node has no dependencies
  R3  a DERIVED node has no ancestor that is FAILS, OPEN, OBSERVATION or UNAUDITED
  R4  every OBSERVATION, FAILS or OPEN node that carries a 'claimed' label names an action
  R5  (--lean) for every node with a 'lean' list:
        - each theorem appears in the report and does not use `sorryAx`;
        - every non-foundation axiom it uses is mapped to a ledger id (meta.lean.axiom_map),
          and that id is the node itself or one of its ancestors in the ledger;
        - a PROVEN node uses no axiom beyond Lean's foundation;
        - a CONDITIONAL node uses at least one axiom mapped to a CONJECTURE node.
"""
import json
import re
import sys
from collections import Counter

KINDS = ["PROVEN", "IMPORT", "CONJECTURE", "CONDITIONAL", "POSTULATE", "INPUT", "DERIVED",
         "OBSERVATION", "FAILS", "OPEN", "UNAUDITED"]
BAD_UPSTREAM = {"FAILS", "OPEN", "OBSERVATION", "UNAUDITED"}


def parse_lean_report(path):
    """Return {theorem: [axioms]} from `#print axioms` output (entries may span lines)."""
    text = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"'([^']+)' depends on axioms: \[(.*?)\]", text, flags=re.S):
        out[m.group(1)] = [a.strip() for a in m.group(2).replace("\n", " ").split(",") if a.strip()]
    for m in re.finditer(r"'([^']+)' does not depend on any axioms", text):
        out[m.group(1)] = []
    return out


def main(argv):
    path = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "derivation_ledger.json"
    lean_path = argv[argv.index("--lean") + 1] if "--lean" in argv else None
    with open(path, encoding="utf-8") as fh:
        ledger = json.load(fh)
    nodes = ledger["nodes"]
    errors = []

    ids = [n["id"] for n in nodes]
    for i, c in Counter(ids).items():
        if c > 1:
            errors.append(f"R0 duplicate id {i}")
    by = {n["id"]: n for n in nodes}
    for n in nodes:
        if n["kind"] not in KINDS:
            errors.append(f"R0 {n['id']}: unknown kind {n['kind']}")
        for d in n["depends_on"]:
            if d not in by:
                errors.append(f"R0 {n['id']}: unknown dependency {d}")

    memo, stack = {}, set()

    def ancestors(i):
        if i in memo:
            return memo[i]
        if i in stack:
            errors.append(f"R0 cycle through {i}")
            return set()
        stack.add(i)
        out = set()
        for d in by[i]["depends_on"]:
            if d in by:
                out.add(d)
                out |= ancestors(d)
        stack.discard(i)
        memo[i] = out
        return out

    for n in nodes:
        anc = ancestors(n["id"])
        kinds = {by[a]["kind"] for a in anc}
        if n["kind"] == "PROVEN" and not kinds <= {"PROVEN", "IMPORT"}:
            errors.append(f"R1 {n['id']}: PROVEN node rests on {sorted(kinds - {'PROVEN', 'IMPORT'})}")
        if n["kind"] == "CONDITIONAL":
            allowed = {"PROVEN", "IMPORT", "CONJECTURE", "CONDITIONAL"}
            if not kinds <= allowed:
                errors.append(f"R1b {n['id']}: CONDITIONAL node rests on {sorted(kinds - allowed)}")
            if "CONJECTURE" not in kinds:
                errors.append(f"R1b {n['id']}: CONDITIONAL node rests on no CONJECTURE")
        if n["kind"] in ("IMPORT", "CONJECTURE") and n["depends_on"]:
            errors.append(f"R2 {n['id']}: {n['kind']} node has dependencies")
        if n["kind"] == "DERIVED" and kinds & BAD_UPSTREAM:
            errors.append(f"R3 {n['id']}: DERIVED node rests on {sorted(kinds & BAD_UPSTREAM)}")
        if n.get("claimed") and n["kind"] in ("OBSERVATION", "FAILS", "OPEN") and not n.get("action"):
            errors.append(f"R4 {n['id']}: no action named")

    lean_rows = []
    if lean_path:
        report = parse_lean_report(lean_path)
        lmeta = ledger["meta"].get("lean", {})
        foundation = set(lmeta.get("foundation_axioms", []))
        amap = lmeta.get("axiom_map", {})
        for n in nodes:
            for thm in n.get("lean", []):
                if thm not in report:
                    errors.append(f"R5 {n['id']}: theorem {thm} not in the Lean report")
                    continue
                axs = report[thm]
                if "sorryAx" in axs:
                    errors.append(f"R5 {n['id']}: {thm} uses sorry")
                extra = [a for a in axs if a not in foundation and a != "sorryAx"]
                mapped = []
                for a in extra:
                    if a not in amap:
                        errors.append(f"R5 {n['id']}: {thm} uses unmapped axiom {a}")
                        continue
                    lid = amap[a]
                    mapped.append(lid)
                    if lid != n["id"] and lid not in ancestors(n["id"]):
                        errors.append(f"R5 {n['id']}: {thm} uses {a} ({lid}), which the ledger does not list upstream")
                if n["kind"] == "PROVEN" and extra:
                    errors.append(f"R5 {n['id']}: PROVEN, but {thm} uses {extra}")
                if n["kind"] == "CONDITIONAL" and not any(by.get(l, {}).get("kind") == "CONJECTURE" for l in mapped):
                    errors.append(f"R5 {n['id']}: CONDITIONAL, but {thm} uses no conjecture")
                lean_rows.append((n["id"], n["kind"], thm, mapped))

    count = Counter(n["kind"] for n in nodes)
    print("UGCT derivation ledger:", ledger["meta"]["date"])
    print("nodes:", len(nodes))
    for k in KINDS:
        print(f"  {k:<12}{count.get(k, 0):>3}")

    claims = [n for n in nodes if "claimed" in n]
    print(f"\nmanuscript claims in the ledger: {len(claims)}")
    moved = Counter((n["claimed"], n["kind"]) for n in claims)
    for (was, now), c in sorted(moved.items()):
        print(f"  claimed {was:<8} -> audited {now:<12}{c:>3}")

    print("\nwhat each claim rests on (P = postulates, I = measured inputs, X = failing/open/observation/unaudited nodes)")
    print(f"{'id':<5}{'audited':<12}{'P':>3}{'I':>3}{'X':>3}  {'gates failed':<16} title")
    for n in claims:
        anc = ancestors(n["id"])
        p = sorted(a for a in anc if by[a]["kind"] == "POSTULATE")
        i = sorted(a for a in anc if by[a]["kind"] == "INPUT")
        x = sorted(a for a in anc if by[a]["kind"] in BAD_UPSTREAM)
        gates = ",".join(n.get("gates_failed", [])) or "-"
        print(f"{n['id']:<5}{n['kind']:<12}{len(p):>3}{len(i):>3}{len(x):>3}  {gates:<16} {n['title'][:70]}")

    if lean_path:
        print("\nmachine-checked by Lean (axioms beyond Lean's foundation, as ledger ids)")
        for nid, kind, thm, mapped in lean_rows:
            print(f"  {nid:<4}{kind:<12}{thm:<58} {', '.join(mapped) if mapped else 'none'}")

    derived = [n for n in nodes if n["kind"] == "DERIVED"]
    print("\nheadline")
    print(f"  postulates                           {count.get('POSTULATE', 0)}")
    print(f"  measured inputs                      {count.get('INPUT', 0)}")
    print(f"  open conjectures assumed             {count.get('CONJECTURE', 0)}")
    print(f"  theorems proved or recomputed        {count.get('PROVEN', 0)} (+{count.get('CONDITIONAL', 0)} conditional)")
    print(f"  published results available          {count.get('IMPORT', 0)}")
    print(f"  physical outputs with status DERIVED {len(derived)}")
    print(f"  observations                         {count.get('OBSERVATION', 0)}")
    print(f"  failing                              {count.get('FAILS', 0)}")
    print(f"  open / unaudited                     {count.get('OPEN', 0)} / {count.get('UNAUDITED', 0)}")
    if lean_path:
        print(f"  nodes backed by Lean theorems        {len({r[0] for r in lean_rows})}")

    gate_hits = Counter(g for n in claims for g in n.get("gates_failed", []))
    print("\ngate failures across claims:", ", ".join(f"{g}:{c}" for g, c in sorted(gate_hits.items(), key=lambda t: int(t[0][1:]))))

    if errors:
        print("\nLEDGER INCONSISTENT")
        for e in errors:
            print("  ", e)
        return 1
    print("\nledger consistent (rules R0-R4" + (", R5 against the Lean report)" if lean_path else ")"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
