#!/usr/bin/env python3
"""Journal derivation fields for the frontier records: the same as emit_journal_semantic_payloads.py.

Until 2026-11-27 this script overwrote the certificates with typed values (among them a Pfaffian interval, a proton
c_p interval of [3.84, 4.06], a Y4 count of 1847 and journal status SOURCE_BACKED_COMPLETE for every item) and wrote
theorem text and derivation scripts that re-emitted the typed numbers. The journal fields are now taken from each
record by emit_journal_semantic_payloads.py; this entry point runs it, for the workflows that call it by this name.

Run from the repository root:  python3 data_room/scripts/emit_journal_derivations.py
"""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("emit_journal_semantic_payloads",
                                              Path(__file__).with_name("emit_journal_semantic_payloads.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

if __name__ == "__main__":
    sys.exit(mod.main())
