#!/usr/bin/env python3
"""Fetch public ancillary files for Jefferson-Turner IntersectionNumbers.

The paper arXiv:2206.11527 supplies IntersectionNumbers.m and example notebook
as ancillary files. This script downloads them into sources/ and records SHA256
hashes for audit/provenance. It does not require Mathematica; execution of the
Mathematica package is handled separately.
"""
import hashlib
import json
import urllib.request
from pathlib import Path

SOURCES = Path("sources")
REPORTS = Path("reports")
SOURCES.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

FILES = {
    "IntersectionNumbers.m": "https://arxiv.org/src/2206.11527/anc/IntersectionNumbers.m",
    "Intersection-Number-Examples.nb": "https://arxiv.org/src/2206.11527/anc/Intersection-Number-Examples.nb"
}

report = {"status": "INTERSECTIONNUMBERS_ANCILLARY_FETCH_RAN", "files": {}}
for name, url in FILES.items():
    out = SOURCES / name
    try:
        with urllib.request.urlopen(url, timeout=90) as r:
            data = r.read()
        out.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        report["files"][name] = {
            "url": url,
            "downloaded": True,
            "path": str(out),
            "bytes": len(data),
            "sha256": digest
        }
    except Exception as exc:
        report["files"][name] = {"url": url, "downloaded": False, "error": str(exc)}

REPORTS.joinpath("intersectionnumbers_ancillary_report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
