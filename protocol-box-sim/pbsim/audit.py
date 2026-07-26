"""Immutable audit log (sections 22.1-22.5).

Every fax reception is treated as a forensic event. Entries are append-only and
each carries the hash of the previous entry, so a tampered row breaks the chain
the same way the spec's LUKS2/SGX-sealed Postgres log is meant to.
"""

import hashlib
import json


class AuditLogger:
    def __init__(self, case_id, device_serial="PB8-2024-001"):
        self.case_id = case_id
        self.device_serial = device_serial
        self.entries = []
        self._prev = "0" * 64
        self._clock = 0.0

    def advance(self, seconds):
        self._clock += seconds

    @property
    def clock(self):
        return round(self._clock, 3)

    def log(self, event, **fields):
        row = {
            "seq": len(self.entries) + 1,
            "t_sec": self.clock,
            "event": event,
            "case_id": self.case_id,
            "device_serial": self.device_serial,
            **fields,
        }
        payload = json.dumps(row, sort_keys=True, default=str)
        row["prev_hash"] = self._prev
        row["row_hash"] = hashlib.sha256((self._prev + payload).encode()).hexdigest()
        self._prev = row["row_hash"]
        self.entries.append(row)
        return row

    def verify_chain(self):
        prev = "0" * 64
        for row in self.entries:
            body = {k: v for k, v in row.items() if k not in ("prev_hash", "row_hash")}
            payload = json.dumps(body, sort_keys=True, default=str)
            expected = hashlib.sha256((prev + payload).encode()).hexdigest()
            if expected != row["row_hash"] or row["prev_hash"] != prev:
                return False, row["seq"]
            prev = row["row_hash"]
        return True, None

    def render(self):
        """Human-readable form matching the log lines quoted in section 22."""
        out = []
        for row in self.entries:
            fields = " | ".join(
                f"{k}: {v}"
                for k, v in row.items()
                if k not in ("seq", "t_sec", "event", "case_id", "device_serial",
                             "prev_hash", "row_hash")
            )
            out.append(f"[{row['t_sec']:>8.2f}s] {row['event']:<20} | {fields}")
        return "\n".join(out)
