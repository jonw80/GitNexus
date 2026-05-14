#!/usr/bin/env python3
"""Bootstrap Esole-Yau source material for the Ewx Chow presentation.

This step downloads public arXiv source/PDF endpoints when GitHub Actions has
network access and searches for resolution/blowup/SR/proper-transform terms. It
is intentionally conservative: it does not invent quotient ideals. It produces a
machine-readable report and source snippets that can be used to populate
`data/esole_yau_ewx_resolved_ambient_chow.json`.
"""
import json
import re
import tarfile
import urllib.request
import zipfile
from pathlib import Path

DATA = Path('data')
REPORTS = Path('reports')
SOURCES = Path('sources')
for p in [DATA, REPORTS, SOURCES]:
    p.mkdir(exist_ok=True)

ARXIV_SOURCES = {
    '1107.0733': 'https://arxiv.org/e-print/1107.0733',
    '1407.1867': 'https://arxiv.org/e-print/1407.1867',
    '1108.1794': 'https://arxiv.org/e-print/1108.1794',
    '1703.00905': 'https://arxiv.org/e-print/1703.00905'
}

PATTERNS = [
    r'E_\{?wx\}?', r'Ewx', r'blow[- ]?up', r'small resolution',
    r'Stanley', r'Reisner', r'proper transform', r'linear equivalence',
    r'A_\{?4\}?', r'SU\(5\)', r'exceptional divisor', r'Cartan'
]
COMPILED = [re.compile(p, re.I) for p in PATTERNS]

def download(url, path):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            path.write_bytes(r.read())
        return True, None
    except Exception as exc:
        return False, str(exc)

def extract_text_files(archive_path, outdir):
    extracted = []
    try:
        if tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path) as tf:
                tf.extractall(outdir)
        elif zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path) as zf:
                zf.extractall(outdir)
        else:
            return []
        for p in outdir.rglob('*'):
            if p.is_file() and p.suffix.lower() in {'.tex', '.txt', '.sty', '.bbl'}:
                extracted.append(p)
    except Exception:
        return []
    return extracted

def snippets_from_file(path):
    try:
        text = path.read_text(errors='ignore')
    except Exception:
        return []
    snippets = []
    for pattern in COMPILED:
        for m in pattern.finditer(text):
            a = max(0, m.start() - 500)
            b = min(len(text), m.end() + 500)
            snippets.append({'pattern': pattern.pattern, 'file': str(path), 'snippet': text[a:b]})
            if len(snippets) >= 30:
                return snippets
    return snippets

report = {'status': 'SOURCE_BOOTSTRAP_RAN', 'downloads': {}, 'snippet_count': 0, 'snippets_file': 'reports/esole_yau_source_snippets.json'}
all_snippets = []
for arxiv_id, url in ARXIV_SOURCES.items():
    archive = SOURCES / f'{arxiv_id}.src'
    ok, err = download(url, archive)
    report['downloads'][arxiv_id] = {'url': url, 'downloaded': ok, 'error': err}
    if not ok:
        continue
    outdir = SOURCES / arxiv_id
    outdir.mkdir(exist_ok=True)
    files = extract_text_files(archive, outdir)
    report['downloads'][arxiv_id]['text_files'] = len(files)
    for f in files:
        all_snippets.extend(snippets_from_file(f))

report['snippet_count'] = len(all_snippets)
Path('reports/esole_yau_source_snippets.json').write_text(json.dumps(all_snippets, indent=2, sort_keys=True))
Path('reports/esole_yau_source_bootstrap_report.json').write_text(json.dumps(report, indent=2, sort_keys=True))
print(json.dumps(report, indent=2, sort_keys=True))
