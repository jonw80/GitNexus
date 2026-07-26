"""pb-ocr: OpenCV preprocessing + Tesseract 5 LSTM extraction.

Models section 12.2 (deskew / denoise / adaptive threshold / DPI normalise) and
section 12.3 (engine configuration, 60% confidence floor) as a character-level
degradation process, so downstream stages see text that fails the way real fax
OCR fails rather than clean ground truth.
"""

import re

from .spec import OCR_CONFIG

# Substitution pairs Tesseract actually confuses on 200 DPI bitonal fax input.
# Digit/letter collisions dominate because fax kills the fine strokes that
# distinguish them.
CONFUSIONS = {
    "0": "O", "O": "0", "1": "l", "l": "1", "I": "1", "5": "S", "S": "5",
    "8": "B", "B": "8", "2": "Z", "Z": "2", "6": "G", "G": "6", "9": "g",
    "D": "0", "Q": "O", "U": "V", "c": "e", "e": "c", "t": "f", "n": "h",
    "m": "rn", "d": "cl", "w": "vv", "-": "_", ".": ",", ",": ".",
}

HW_OPEN, HW_CLOSE = "[[hw]]", "[[/hw]]"


def _preprocess(source_quality, log):
    """Section 12.2 preprocess_fax_image(): returns a quality multiplier.

    Each step recovers some of the loss the transport introduced. Nothing here
    can recover information the channel destroyed outright (dropped scanlines),
    which is exactly why page loss stays a hard failure downstream.
    """
    steps = []
    recovery = 1.0

    skew = source_quality.get("skew_deg", 0.0)
    if abs(skew) > 0.5:
        # Hough-transform deskew; residual error after warp is ~15% of input.
        steps.append(f"deskew({skew:.1f}deg -> {skew * 0.15:.2f}deg)")
        recovery *= 1.0 + min(0.30, abs(skew) * 0.030)
    else:
        steps.append("deskew(skipped, <0.5deg)")

    noise = source_quality.get("noise", 0.0)
    if noise > 0:
        # fastNlMeansDenoising(h=10) removes speckle but softens thin strokes.
        steps.append(f"fastNlMeansDenoising(h=10) noise {noise:.2f}")
        recovery *= 1.0 + min(0.25, noise * 0.9)

    steps.append("adaptiveThreshold(GAUSSIAN_C, block=11, C=2)")
    fade = source_quality.get("thermal_fade", 0.0)
    if fade > 0.25:
        # Adaptive thresholding on a faded original erodes glyphs to fragments.
        steps.append(f"WARN: faded original ({fade:.2f}) erodes strokes")
        recovery *= 1.0 - min(0.20, (fade - 0.25) * 0.5)

    dpi = source_quality.get("dpi", OCR_CONFIG["assumed_input_dpi"])
    scale = OCR_CONFIG["target_dpi"] / OCR_CONFIG["assumed_input_dpi"]
    steps.append(f"resize(INTER_CUBIC, x{scale:.2f}) {dpi} -> {OCR_CONFIG['target_dpi']} DPI")
    if dpi < OCR_CONFIG["assumed_input_dpi"]:
        # preprocess.py hardcodes a 200 DPI assumption. A 100 DPI standard-mode
        # fax is upscaled by the wrong factor and interpolation invents strokes.
        steps.append(f"WARN: preprocess.py assumes 200 DPI, input was {dpi} DPI")
        recovery *= 0.80

    log(steps)
    return recovery


def _base_error_rate(source_quality, recovery):
    """Per-character error probability for machine-printed text."""
    dpi = source_quality.get("dpi", 200)
    # Floor is set so a clean 200 DPI typed page lands near 99.4% character
    # accuracy, consistent with Tesseract 5 LSTM on bitonal fax input.
    err = 0.0025
    err += max(0.0, (200 - dpi) / 200.0) * 0.16
    err += source_quality.get("noise", 0.0) * 0.10
    err += source_quality.get("thermal_fade", 0.0) * 0.20
    err += min(abs(source_quality.get("skew_deg", 0.0)), 8.0) * 0.004
    if source_quality.get("second_generation"):
        # A fax of a fax: generational loss compounds.
        err *= 1.45
    return max(0.001, err / recovery)


def _degrade_token(token, err_rate, rng):
    """Apply character-level noise to one token, return (token, n_errors)."""
    out = []
    errors = 0
    for ch in token:
        if rng.random() < err_rate:
            errors += 1
            roll = rng.random()
            if roll < 0.62 and ch in CONFUSIONS:
                out.append(CONFUSIONS[ch])
            elif roll < 0.80:
                continue  # dropped glyph
            elif roll < 0.92:
                out.append("")  # ligature collapse
            else:
                out.append(rng.choice("il1c0oB8S5"))
        else:
            out.append(ch)
    return "".join(out), errors


def run_ocr(case, rng, audit):
    """Preprocess + extract. Returns text, per-token confidences, and metrics."""
    logged = {}

    def _log(steps):
        logged["preprocess_steps"] = steps

    recovery = _preprocess(case.source_quality, _log)
    err_rate = _base_error_rate(case.source_quality, recovery)
    hw_multiplier = 6.5  # handwriting is where Tesseract LSTM falls apart

    raw = case.raw_text

    # Pages the channel never delivered cannot be OCR'd. Split on the form-feed
    # marker the corpus uses for page boundaries and truncate.
    if case.source_quality.get("page_loss", 0):
        pages = raw.split("\f")
        kept = max(1, len(pages) - case.source_quality["page_loss"])
        raw = "\f".join(pages[:kept])

    tokens_out = []
    confidences = []
    total_chars = 0
    total_errors = 0
    handwritten_tokens = 0

    in_hw = False
    for line in raw.split("\n"):
        line_tokens = []
        for token in line.split(" "):
            if not token:
                line_tokens.append("")
                continue
            if HW_OPEN in token:
                in_hw = True
                token = token.replace(HW_OPEN, "")
            close_here = HW_CLOSE in token
            if close_here:
                token = token.replace(HW_CLOSE, "")
            if not token:
                if close_here:
                    in_hw = False
                continue

            rate = err_rate * (hw_multiplier if in_hw else 1.0)
            rate = min(rate, 0.55)
            degraded, errors = _degrade_token(token, rate, rng)
            total_chars += len(token)
            total_errors += errors
            if in_hw:
                handwritten_tokens += 1

            # Tesseract reports per-word confidence; it tracks observed error
            # density closely but never reports a clean word at 100%.
            conf = 0.985 - (errors / max(1, len(token))) * 0.95 - rate * 0.55
            conf = max(0.05, min(0.99, conf + rng.uniform(-0.03, 0.03)))
            confidences.append((degraded, round(conf, 3)))
            line_tokens.append(degraded)
            if close_here:
                in_hw = False
        tokens_out.append(" ".join(line_tokens))

    text = "\n".join(tokens_out)
    text = re.sub(r"[ \t]+\n", "\n", text)

    avg_conf = sum(c for _, c in confidences) / max(1, len(confidences))
    low_conf = [t for t, c in confidences if c < OCR_CONFIG["confidence_threshold"]]
    cer = total_errors / max(1, total_chars)

    # Forms drop to PSM 6 when PSM 3's layout analysis fragments the columns.
    psm = OCR_CONFIG["psm_form_fallback"] if case.is_form else OCR_CONFIG["psm_default"]

    result = {
        "text": text,
        "avg_confidence": round(avg_conf, 4),
        "char_error_rate": round(cer, 4),
        "token_count": len(confidences),
        "low_confidence_tokens": len(low_conf),
        "low_confidence_sample": low_conf[:8],
        "handwritten_tokens": handwritten_tokens,
        "psm": psm,
        "oem": OCR_CONFIG["oem"],
        "languages": OCR_CONFIG["languages"],
        "preprocess_steps": logged.get("preprocess_steps", []),
        "pages_ocrd": raw.count("\f") + 1,
    }

    audit.log(
        "OCR_COMPLETE",
        avg_confidence=result["avg_confidence"],
        cer=result["char_error_rate"],
        psm=psm,
        low_conf_tokens=result["low_confidence_tokens"],
        below_threshold=avg_conf < OCR_CONFIG["confidence_threshold"],
    )
    return result
