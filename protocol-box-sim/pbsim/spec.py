"""Constants transcribed from Protocol Box Master Internal Build File v4.1.

Every value here has a citation to the section of the build file it came from so
the simulation can be audited against the spec rather than against itself.
"""

# --- Section 2.1 / 3.2 / 4.2 / 5.2 / 6.2: SKU capability envelopes -----------
SKU_PROFILES = {
    "PB-4": {
        "processor": "Rockchip RK3588 (6 TOPS NPU)",
        "concurrent_sessions": 4,
        "ocr_pages_per_min": 8.0,
        "ttfa_budget_sec": 30.0,
        "nlu_device": "rknpu0",
        "classified_capable": False,
    },
    "PB-8": {
        "processor": "Rockchip RK3588 (6 TOPS NPU)",
        "concurrent_sessions": 8,
        "ocr_pages_per_min": 15.0,
        "ttfa_budget_sec": 25.0,
        "nlu_device": "rknpu0",
        "classified_capable": False,
    },
    "PB-E": {
        "processor": "Intel Xeon D-1733NT",
        "concurrent_sessions": 96,
        "ocr_pages_per_min": 60.0,
        "ttfa_budget_sec": 20.0,
        "nlu_device": "myriad0",
        "classified_capable": False,
    },
    "PB-S": {
        "processor": "Intel Xeon D + SGX",
        "concurrent_sessions": 8,
        "ocr_pages_per_min": 30.0,
        "ttfa_budget_sec": 25.0,
        "nlu_device": "myriad0",
        "classified_capable": True,
    },
}

# --- Section 12.1: pipeline stage latency envelopes (seconds) ---------------
# Stage 1 (T.30 ingest) and stage 8 (outbound) are excluded from TTFA, which the
# spec defines as "from end of fax transmission".
STAGE_LATENCY = {
    "detect": (0.02, 0.10),
    "preprocess": (1.0, 2.0),
    "extract_text": (2.0, 5.0),
    "classify": (0.05, 0.50),
    "extract_entities": (0.05, 0.50),
    "execute": (1.0, 5.0),
}

# --- Section 12.3: OCR engine configuration --------------------------------
OCR_CONFIG = {
    "engine": "Tesseract 5.3.1",
    "oem": 1,
    "psm_default": 3,
    "psm_form_fallback": 6,
    "languages": "eng+spa",
    "confidence_threshold": 0.60,
    "target_dpi": 300,
    "assumed_input_dpi": 200,
}

# --- Section 12.5: modulation ladder ---------------------------------------
# Ordered best-first. The T.30 negotiation walks down this ladder as the
# measured line quality degrades.
MODULATIONS = [
    {"standard": "V.34", "bps": 33600, "modulation": "Shell mapping", "min_line_quality": 0.92},
    {"standard": "V.17", "bps": 14400, "modulation": "TCM", "min_line_quality": 0.72},
    {"standard": "V.29", "bps": 9600, "modulation": "QAM", "min_line_quality": 0.55},
    {"standard": "V.27ter", "bps": 4800, "modulation": "DPSK", "min_line_quality": 0.0},
]

# --- Section 13.2: intent classes as shipped in v4.1 ------------------------
INTENT_CLASSES = [
    "RECORDS_REQUEST",
    "PURCHASE_ORDER",
    "LAB_RESULT",
    "PRESCRIPTION_REFILL",
    "INSURANCE_DENIAL",
    "CLARIFICATION_NEEDED",
    "SPAM_OTHER",
]

INTENT_ACTIONS = {
    "RECORDS_REQUEST": "Query EMR, assemble, refax",
    "PURCHASE_ORDER": "Create sales order in ERP",
    "LAB_RESULT": "Route to provider inbox",
    "PRESCRIPTION_REFILL": "Route to pharmacy queue",
    "INSURANCE_DENIAL": "Route to billing dept",
    "CLARIFICATION_NEEDED": "Route to human review",
    "SPAM_OTHER": "Archive only",
}

# Section 13.5: classify.py hardcodes confidence_threshold=0.6.
INTENT_CONFIDENCE_THRESHOLD = 0.60

# --- Section 13.4: NER entity inventory ------------------------------------
ENTITY_TYPES = [
    "PATIENT_NAME",
    "DATE_OF_BIRTH",
    "MRN",
    "PART_NUMBER",
    "QUANTITY",
    "PO_NUMBER",
    "FAX_NUMBER",
    "FACILITY_NAME",
]

# --- Section 17.3: outbound fax error codes --------------------------------
FAX_ERROR_CODES = {
    "E001": {"desc": "No dial tone", "action": "Check line"},
    "E002": {"desc": "Busy signal", "action": "Auto-retry"},
    "E003": {"desc": "No answer", "action": "Retry in 5 min"},
    "E004": {"desc": "Voice answered", "action": "Wrong number"},
    "E005": {"desc": "Handshake failure", "action": "Reduce speed"},
    "E006": {"desc": "Page error", "action": "Retry page"},
    "E007": {"desc": "Remote disconnect", "action": "Retry job"},
}

# --- Section 17.4 / E.5.1: /etc/protocolbox/retry.yaml ----------------------
RETRY_POLICY = {
    "max_attempts": 3,
    "initial_delay_seconds": 300,
    "backoff_multiplier": 2.0,
    "max_delay_seconds": 3600,
    "error_overrides": {"E002": {"max_attempts": 5, "initial_delay_seconds": 60}},
    "terminal_errors": ["E001", "E004"],
    "jitter_pct": 0.10,
}

# --- Section 17.2: outbound status state machine ---------------------------
FAX_STATES = {
    "queued": ["dialing", "cancelled"],
    "dialing": ["connecting", "failed"],
    "connecting": ["transmitting", "failed"],
    "transmitting": ["completed", "failed"],
    "completed": [],
    "failed": ["retry_pending"],
    "retry_pending": ["dialing"],
    "cancelled": [],
}

# --- Section 16.3: Ghost Mode go-live criteria ------------------------------
GO_LIVE_CRITERIA = {
    "intent_accuracy": {"threshold": 0.95, "op": ">=", "label": "Intent classification accuracy"},
    "entity_accuracy": {"threshold": 0.90, "op": ">=", "label": "Entity extraction accuracy"},
    "phi_misdirection_rate": {"threshold": 0.0, "op": "==", "label": "False positive rate (PHI misdirection)"},
    "avg_ocr_confidence": {"threshold": 0.85, "op": ">=", "label": "OCR confidence (average)"},
    "sample_size": {"threshold": 100, "op": ">=", "label": "Minimum sample size"},
}

# --- Section 23 / 6.2: classification markings the PB-S posture cares about -
# The v4.1 pipeline has no banner detector; the hardened profile adds one.
CLASSIFICATION_MARKINGS = [
    "TOP SECRET",
    "TOP SECRET//SCI",
    "SECRET//NOFORN",
    "SECRET//REL TO USA",
    "SECRET",
    "CONFIDENTIAL//",
    "CUI//SP-",
    "CUI//",
    "CONTROLLED UNCLASSIFIED INFORMATION",
    "FOUO",
    "FOR OFFICIAL USE ONLY",
]

# Dispositions the harness scores against.
DISPOSITIONS = [
    "AUTO_ACTION",     # closed-loop: ERP/EMR transaction executed and reply faxed
    "ROUTE",           # delivered to a named queue/inbox, no transaction
    "HUMAN_REVIEW",    # parked for an operator
    "ARCHIVE",         # stored, no action
    "QUARANTINE",      # security hold: no OCR export, no auto-reply
]
