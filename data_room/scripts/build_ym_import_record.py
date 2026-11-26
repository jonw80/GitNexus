#!/usr/bin/env python3
"""Build the Yang-Mills import record from the author's status file.

Writes data_room/data/ym_mass_gap_import_certificate.json and data_room/proofs/ym_mass_gap_import_theorem.tex.

Input: data_room/primary/ym/ym_companion_status.json. For each of the four statements the frontier gate checks, it
records the statement's status in the companion volume ("proved", "conditional", "lattice_only" or "open"), the
theorems and pages, what is proved, and what is assumed or open. It also records the volume file (if committed) and
any independent verification.

A flag is true only when its statement is proved as stated (status "proved"). The record has status
VERIFIED_YM_MASS_GAP_COMPANION_IMPORT only if all four flags are true, the volume file is in the repository (and
matches a recorded hash, if one is given), and at least one independent verification is recorded. Otherwise the status
is YM_COMPANION_IMPORT_CONDITIONAL and the reasons are listed in open_items. Every value comes from the status file
or from hashing files; nothing is typed in here.

This replaces the certificate that emit_frontier_closeout_artifacts.py used to type in (status VERIFIED, all flags
true, and a companion hash with no file behind it).

Run from the repository root:  python3 data_room/scripts/build_ym_import_record.py
(exits 1 if the status file is missing or malformed)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

STATUS_FILE = "data_room/primary/ym/ym_companion_status.json"
OUT_JSON = "data_room/data/ym_mass_gap_import_certificate.json"
OUT_TEX = "data_room/proofs/ym_mass_gap_import_theorem.tex"
VERIFIED = "VERIFIED_YM_MASS_GAP_COMPANION_IMPORT"
CONDITIONAL = "YM_COMPANION_IMPORT_CONDITIONAL"
GATES = [("os_axioms", "os_axioms_verified"), ("reflection_positivity", "reflection_positivity_verified"),
         ("rg_convergence", "rg_convergence_verified"), ("spectral_gap", "spectral_gap_lower_bound_positive")]
STATUSES = ("proved", "conditional", "lattice_only", "open")


class StatusFileError(Exception):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(obj: dict) -> str:
    """Same canonical hash as data_room/scripts/verify_frontier_closeout.py."""
    tmp = dict(obj)
    tmp.pop("payload_hash", None)
    return hashlib.sha256(json.dumps(tmp, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def tex_escape(s) -> str:
    out = []
    for ch in str(s):
        out.append({"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
                    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}"}.get(ch, ch))
    return "".join(out)


def load_status(root: Path) -> dict:
    path = root / STATUS_FILE
    if not path.exists():
        raise StatusFileError(f"missing {STATUS_FILE}")
    try:
        st = json.loads(path.read_text())
    except Exception as exc:
        raise StatusFileError(f"unreadable {STATUS_FILE}: {exc}")
    gates = st.get("gates")
    if not isinstance(gates, dict):
        raise StatusFileError("status file has no gates table")
    for name, flag in GATES:
        g = gates.get(name)
        if not isinstance(g, dict):
            raise StatusFileError(f"status file lacks gate {name}")
        if g.get("flag") != flag:
            raise StatusFileError(f"gate {name} names flag {g.get('flag')!r}, expected {flag!r}")
        if g.get("status") not in STATUSES:
            raise StatusFileError(f"gate {name} has status {g.get('status')!r}, expected one of {STATUSES}")
        if not isinstance(g.get("references"), list) or not g["references"]:
            raise StatusFileError(f"gate {name} cites no theorem or page")
    if not isinstance(st.get("companion_volume"), dict):
        raise StatusFileError("status file has no companion_volume entry")
    if not isinstance(st.get("independent_verification"), list):
        raise StatusFileError("independent_verification must be a list")
    return st


def build(root: Path) -> tuple[dict, str]:
    st = load_status(root)
    vol = st["companion_volume"]
    open_items = []

    volume_sha = None
    vfile = vol.get("file")
    if vfile:
        vpath = root / vfile
        if vpath.exists():
            volume_sha = sha256_file(vpath)
            if vol.get("sha256") and vol["sha256"] != volume_sha:
                open_items.append(f"The recorded volume hash {vol['sha256']} differs from the file's {volume_sha}.")
                volume_sha = None
        else:
            open_items.append(f"The companion volume file {vfile} named in the status file is not in the repository.")
    else:
        open_items.append("The companion volume file is not in the repository, so it cannot be hashed.")

    flags, gates = {}, {}
    for name, flag in GATES:
        g = st["gates"][name]
        flags[flag] = g["status"] == "proved"
        gates[name] = {k: g.get(k) for k in ("flag", "status", "statement", "references", "proved", "assumed_or_open")}
        if not flags[flag]:
            open_items.append(f"{flag}: {g['status']} ({'; '.join(g['references'])}). {g.get('assumed_or_open') or ''}".strip())
    if not st["independent_verification"]:
        open_items.append("No independent verification of the companion volume is recorded.")

    verified = all(flags.values()) and volume_sha is not None and bool(st["independent_verification"])
    record = {
        "schema_version": "UGCT_YM_MASS_GAP_IMPORT_RECORD_V1",
        "status": VERIFIED if verified else CONDITIONAL,
        "fully_certified": verified,
        "companion_volume_sha256": volume_sha,
        "companion_volume": {"title": vol.get("title"), "file": vfile, "recorded_sha256": vol.get("sha256"),
                             "note": vol.get("note")},
        **flags,
        "gates": gates,
        "independent_verification": st["independent_verification"],
        "pipelines": st.get("pipelines"),
        "source_status_file": STATUS_FILE,
        "source_status_sha256": sha256_file(root / STATUS_FILE),
        "status_recorded": st.get("recorded"),
        "status_source": st.get("source"),
        "verification_rule": "a flag is true only if its statement is proved as stated; verified only if all four are, "
                             "the volume file is committed (and matches any recorded hash), and an independent "
                             "verification is recorded",
        "open_items": [] if verified else open_items,
    }
    record["payload_hash"] = canonical_hash(record)

    lines = [
        r"\section*{Yang--Mills import record}",
        "This file is generated by \\texttt{data\\_room/scripts/build\\_ym\\_import\\_record.py} from "
        "\\texttt{" + tex_escape(STATUS_FILE) + "}. It records the status of the four statements the import needs, "
        "as stated for the companion volume. It is a record, not a theorem.",
        "",
        "Companion volume: " + tex_escape(vol.get("title") or "n/a") + ". File: "
        + ("\\texttt{" + tex_escape(vfile) + "}" if vfile else "not in the repository") + ". SHA-256: "
        + ("\\texttt{" + volume_sha + "}" if volume_sha else "none") + ". "
        + tex_escape(st.get("source") or ""),
        "",
        r"\begin{itemize}",
    ]
    for name, flag in GATES:
        g = st["gates"][name]
        lines.append(f"\\item \\textbf{{{tex_escape(g.get('statement') or name)}}} (\\texttt{{{tex_escape(flag)}}}): "
                     f"status \\texttt{{{tex_escape(g['status'])}}}. References: {tex_escape('; '.join(g['references']))}. "
                     f"Proved: {tex_escape(g.get('proved') or 'nothing recorded')} "
                     f"Assumed or open: {tex_escape(g.get('assumed_or_open') or 'nothing recorded')}")
    lines += [r"\end{itemize}", f"Status: \\texttt{{{tex_escape(record['status'])}}}."]
    if record["open_items"]:
        lines += [r"Open items:", r"\begin{enumerate}"] + [f"\\item {tex_escape(i)}" for i in record["open_items"]] + [r"\end{enumerate}"]
    return record, "\n".join(lines) + "\n"


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try:
        record, tex = build(root)
    except StatusFileError as exc:
        print(f"FAILED: {exc}")
        return 1
    (root / OUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (root / OUT_TEX).parent.mkdir(parents=True, exist_ok=True)
    (root / OUT_JSON).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (root / OUT_TEX).write_text(tex)
    print(json.dumps({k: record[k] for k in ("status", "companion_volume_sha256", "os_axioms_verified",
                                             "reflection_positivity_verified", "rg_convergence_verified",
                                             "spectral_gap_lower_bound_positive")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
