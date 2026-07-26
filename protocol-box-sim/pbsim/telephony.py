"""pb-telephony: T.30 inbound termination and outbound fax origination.

Implements section 12.4 (T.30 phases A-E), 12.5 (modulation ladder),
17.2 (outbound status state machine), 17.3 (error codes) and
17.4 (retry policy) of the build file.
"""

import hashlib
import random

from .spec import FAX_ERROR_CODES, FAX_STATES, MODULATIONS, RETRY_POLICY


def negotiate_modulation(line_quality):
    """T.30 Phase B: pick the fastest modulation the line will carry."""
    for mod in MODULATIONS:
        if line_quality >= mod["min_line_quality"]:
            return mod
    return MODULATIONS[-1]


class InboundFaxSession:
    """One inbound T.30 call, from ring detect through EOP/MCF."""

    def __init__(self, case, rng, audit):
        self.case = case
        self.rng = rng
        self.audit = audit

    def receive(self):
        case = self.case
        lq = case.line_quality

        # Phase A: CNG/CED exchange. 90V ring detected by the Si3050 DAA.
        # Phase B: CSI/TSI exchange, DCS command, capability negotiation.
        mod = negotiate_modulation(lq)

        # ECM is negotiated off on the worst lines; without it, page errors are
        # not retransmitted and corrupt scanlines reach the spool.
        ecm_active = lq >= 0.50

        # Phase C: image transfer. A 1728x1100 fine-mode page is ~ 1.1 Mbit
        # before MMR compression; MMR on text typically lands near 12:1.
        bits_per_page = 1_100_000 / 12.0
        transfer_sec = (bits_per_page / mod["bps"]) * case.pages
        # Training, TCF and inter-page handshakes add fixed overhead per page.
        transfer_sec += 6.0 * case.pages + 8.0

        # Page errors. Without ECM these become permanent scanline damage.
        page_errors = 0
        for _ in range(case.pages):
            if self.rng.random() > lq:
                page_errors += 1
        lost_pages = case.source_quality.get("page_loss", 0)

        received_pages = max(0, case.pages - lost_pages)
        uncorrected_errors = 0 if ecm_active else page_errors
        if not ecm_active:
            # Retransmission attempts inflate the call duration.
            transfer_sec += 4.0 * page_errors

        self.audit.log(
            "FAX_CONNECT",
            remote_id=case.caller_id,
            protocol="T.30",
            speed=mod["bps"],
            modulation=mod["standard"],
            ecm=ecm_active,
            did=case.did,
        )

        # Phase D/E: EOP, MCF confirmation, DCN disconnect.
        # Digital seal (section 22.2): hash the TIFF before any OCR touches it.
        payload = f"{case.case_id}|{case.pages}|{case.raw_text}".encode("utf-8")
        tiff_hash = hashlib.sha256(payload).hexdigest()
        self.audit.log(
            "FILE_CREATED",
            hash=f"sha256:{tiff_hash}",
            path=f"/spool/fax-{case.case_id}.tiff",
            pages=received_pages,
        )

        return {
            "modulation": mod,
            "ecm_active": ecm_active,
            "transfer_sec": round(transfer_sec, 1),
            "pages_sent": case.pages,
            "pages_received": received_pages,
            "pages_lost": lost_pages,
            "uncorrected_page_errors": uncorrected_errors,
            "tiff_sha256": tiff_hash,
        }


class OutboundFaxJob:
    """Outbound reply fax with the section 17.4 retry ladder."""

    def __init__(self, job_id, destination, page_count, rng, audit, line_quality=0.9):
        self.job_id = job_id
        self.destination = destination
        self.page_count = page_count
        self.rng = rng
        self.audit = audit
        self.line_quality = line_quality
        self.state = "queued"
        self.transitions = ["queued"]
        self.attempts = []

    def _transition(self, new_state):
        allowed = FAX_STATES[self.state]
        if new_state not in allowed:
            raise AssertionError(
                f"illegal fax state transition {self.state} -> {new_state}"
            )
        self.state = new_state
        self.transitions.append(new_state)

    def _attempt_outcome(self):
        """Roll one dial attempt against the line model."""
        r = self.rng.random()
        lq = self.line_quality
        if r > 0.06 + (1.0 - lq) * 0.55:
            return None  # success
        # Weight the failure modes the way a real PSTN trunk does.
        roll = self.rng.random()
        if roll < 0.34:
            return "E002"  # busy
        if roll < 0.55:
            return "E003"  # no answer
        if roll < 0.75:
            return "E005"  # handshake failure
        if roll < 0.88:
            return "E007"  # remote disconnect
        if roll < 0.96:
            return "E006"  # page error
        return "E004"  # voice answered

    def send(self):
        policy = RETRY_POLICY
        max_attempts = policy["max_attempts"]
        delay = policy["initial_delay_seconds"]
        total_delay = 0.0
        attempt = 0

        while True:
            attempt += 1
            if self.state == "retry_pending":
                self._transition("dialing")
            else:
                self._transition("dialing")
            err = self._attempt_outcome()
            if err is None:
                self._transition("connecting")
                self._transition("transmitting")
                self._transition("completed")
                confirmation = hashlib.sha256(
                    f"{self.job_id}|{self.destination}|{attempt}".encode()
                ).hexdigest()[:12].upper()
                self.attempts.append({"attempt": attempt, "result": "completed"})
                self.audit.log(
                    "FAX_SENT",
                    fax_id=self.job_id,
                    destination=self.destination,
                    pages=self.page_count,
                    attempts=attempt,
                    confirmation_code=confirmation,
                )
                return {
                    "status": "completed",
                    "attempts": attempt,
                    "confirmation_code": confirmation,
                    "queue_delay_sec": round(total_delay, 1),
                    "transitions": self.transitions,
                }

            self._transition("failed")
            self.attempts.append(
                {"attempt": attempt, "result": "failed", "error": err,
                 "desc": FAX_ERROR_CODES[err]["desc"]}
            )

            if err in policy["terminal_errors"]:
                self.audit.log(
                    "FAX_FAILED", fax_id=self.job_id, error_code=err,
                    reason=FAX_ERROR_CODES[err]["desc"], terminal=True, attempts=attempt,
                )
                return {
                    "status": "failed", "error_code": err, "terminal": True,
                    "attempts": attempt, "queue_delay_sec": round(total_delay, 1),
                    "transitions": self.transitions,
                }

            override = policy["error_overrides"].get(err, {})
            effective_max = override.get("max_attempts", max_attempts)
            if attempt >= effective_max:
                self.audit.log(
                    "FAX_FAILED", fax_id=self.job_id, error_code=err,
                    reason="retries exhausted", attempts=attempt,
                )
                return {
                    "status": "failed", "error_code": err, "terminal": False,
                    "attempts": attempt, "queue_delay_sec": round(total_delay, 1),
                    "transitions": self.transitions,
                }

            base = override.get("initial_delay_seconds", policy["initial_delay_seconds"])
            step = min(
                base * (policy["backoff_multiplier"] ** (attempt - 1)),
                policy["max_delay_seconds"],
            )
            # Section 17.4: 10% jitter to avoid a thundering herd on recovery.
            step *= 1.0 + self.rng.uniform(-policy["jitter_pct"], policy["jitter_pct"])
            total_delay += step
            self._transition("retry_pending")
