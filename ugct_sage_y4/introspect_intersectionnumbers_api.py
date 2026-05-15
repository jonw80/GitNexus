#!/usr/bin/env python3
"""Introspect Jefferson-Turner IntersectionNumbers ancillary files.

This script scans the downloaded Mathematica package and notebook for exported
symbols, usage messages, source contexts, and example calls so the Ewx driver can
be completed from the actual public API rather than guessed symbol names.
"""
import json
import re
from pathlib import Path

SOURCES = Path("sources")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)
PKG = SOURCES / "IntersectionNumbers.m"
NB = SOURCES / "Intersection-Number-Examples.nb"
OUT = REPORTS / "intersectionnumbers_api_introspection.json"
MD = REPORTS / "intersectionnumbers_api_introspection.md"

TARGET_SYMBOLS = [
    "algRanksPattern", "algebraDivisors", "divisors", "divisorsMake",
    "hypersurface", "push", "pushFun", "pushFunction"
]

report = {
    "status": "INTERSECTIONNUMBERS_API_INTROSPECTION_RAN",
    "package_exists": PKG.exists(),
    "notebook_exists": NB.exists(),
    "usage_symbols": [],
    "candidate_definitions": [],
    "source_contexts": {},
    "example_call_lines": []
}

if PKG.exists():
    text = PKG.read_text(errors="ignore")
    usage = re.findall(r'([A-Za-z$][A-Za-z0-9$]*)::usage\s*=\s*"([\s\S]*?)"\s*;', text)
    report["usage_symbols"] = [{"symbol": s, "usage": u[:1000]} for s, u in usage]
    defs = sorted(set(re.findall(r'\n([A-Za-z$][A-Za-z0-9$]*)\s*(?:\[|:=|=|::)', text)))
    interesting = [d for d in defs if re.search(r'Tate|Intersect|Generate|Resolve|Blow|Push|Divisor|Cartan|SU|SO|Sp|E[0-9]', d, re.I)]
    report["candidate_definitions"] = interesting[:500]
    lines_text = text.splitlines()
    for sym in TARGET_SYMBOLS:
        contexts = []
        pat = re.compile(r'\b' + re.escape(sym) + r'\b')
        for i, line in enumerate(lines_text):
            if pat.search(line):
                snippet = "\n".join(lines_text[max(0, i-8): min(len(lines_text), i+18)])
                contexts.append({"line": i+1, "snippet": snippet[:5000]})
                if len(contexts) >= 8:
                    break
        report["source_contexts"][sym] = contexts

if NB.exists():
    nb = NB.read_text(errors="ignore")
    lines = nb.splitlines()
    examples = []
    for i, line in enumerate(lines):
        if re.search(r'Tate|Intersection|Generating|Generate|SU\(|SU5|Cartan|A4|Divisor|Classical|pushFunction|pushFun|divisorsMake|hypersurface', line, re.I):
            snippet = "\n".join(lines[max(0, i-5): min(len(lines), i+8)])
            examples.append({"line": i+1, "snippet": snippet[:3000]})
            if len(examples) >= 100:
                break
    report["example_call_lines"] = examples

OUT.write_text(json.dumps(report, indent=2, sort_keys=True))
lines = ["# IntersectionNumbers API introspection", "", f"Status: `{report['status']}`", f"Package exists: `{report['package_exists']}`", f"Notebook exists: `{report['notebook_exists']}`", "", "## Usage symbols", ""]
for item in report["usage_symbols"][:50]:
    lines.append(f"- `{item['symbol']}`: {item['usage'][:300].replace(chr(10), ' ')}")
lines += ["", "## Candidate definitions", ""]
for sym in report["candidate_definitions"][:100]:
    lines.append(f"- `{sym}`")
lines += ["", "## Source contexts", ""]
for sym, ctxs in report["source_contexts"].items():
    lines.append(f"### `{sym}`")
    for ctx in ctxs[:3]:
        lines.append(f"line {ctx['line']}\n```mathematica\n{ctx['snippet']}\n```\n")
lines += ["", "## Example call snippets", ""]
for ex in report["example_call_lines"][:25]:
    lines.append(f"### line {ex['line']}\n```mathematica\n{ex['snippet']}\n```\n")
MD.write_text("\n".join(lines))

console = {
    "status": report["status"],
    "usage_symbol_count": len(report["usage_symbols"]),
    "candidate_definition_count": len(report["candidate_definitions"]),
    "example_snippet_count": len(report["example_call_lines"]),
    "candidate_definitions": report["candidate_definitions"][:50],
    "source_contexts_preview": {
        sym: [{"line": c["line"], "snippet": c["snippet"][:1000]} for c in ctxs[:2]]
        for sym, ctxs in report["source_contexts"].items()
    },
    "example_snippets_preview": [
        {"line": x["line"], "snippet": x["snippet"][:800]} for x in report["example_call_lines"][:5]
    ]
}
print(json.dumps(console, indent=2, sort_keys=True))
