"""pb-nlp: DistilBERT intent classification (13.5) and NER entity extraction (13.4).

The shipped model is a distilbert-base-uncased classification head fine-tuned on
"50,000 labeled fax samples (healthcare + manufacturing)" (section 13.1). This
module stands in for that head with a weighted lexical evidence model whose
vocabulary coverage deliberately mirrors that training distribution: dense on
clinical and purchase-order language, thin on MRO, office-administrative and
defence-logistics vocabulary the training set never contained.
"""

import math
import re

from .spec import INTENT_CONFIDENCE_THRESHOLD

# Weighted evidence per shipped intent class. Weights approximate the attention
# mass the fine-tuned head puts on each trigger phrase.
LEXICON = {
    "RECORDS_REQUEST": {
        "medical records": 3.2, "release of information": 3.0, "roi request": 2.8,
        "authorization for release": 2.8, "protected health information": 2.4,
        "progress notes": 2.2, "discharge summary": 2.2, "patient records": 2.6,
        "hipaa": 1.6, "date of birth": 1.0, "records request": 3.0,
        "medical record number": 1.8, "chart": 1.2, "requesting records": 2.6,
        "personnel file": 0.9, "employment records": 1.0, "subpoena": 1.1,
        "records": 1.4, "custodian of records": 1.5,
    },
    "PURCHASE_ORDER": {
        "purchase order": 3.4, "p.o. number": 2.6, "po number": 2.6,
        "part number": 2.2, "quantity": 1.8, "unit price": 1.9, "ship to": 1.8,
        "order": 1.5, "line item": 1.7, "sales order": 2.0, "qty": 1.5,
        "delivery date": 1.4, "buyer": 1.2, "vendor": 1.1, "part no": 2.0,
        "each": 0.6, "total": 0.8, "confirm receipt": 0.9, "reorder": 1.6,
        "requisition": 1.3, "supply": 0.8, "catalog": 0.9, "item": 0.7,
        "pedido": 1.4, "cantidad": 1.2, "numero de parte": 1.6,
    },
    "LAB_RESULT": {
        "laboratory": 2.6, "lab result": 3.2, "pathology": 2.8, "specimen": 2.4,
        "reference range": 2.6, "cbc": 2.0, "metabolic panel": 2.4,
        "collected": 1.2, "abnormal": 1.4, "hematology": 2.4, "culture": 1.6,
    },
    "PRESCRIPTION_REFILL": {
        "refill": 3.2, "prescription": 2.8, "rx": 2.4, "pharmacy": 2.2,
        "dispense": 2.0, "sig:": 1.8, "mg": 0.7, "days supply": 2.0,
        "ndc": 1.8, "dea": 1.4,
    },
    "INSURANCE_DENIAL": {
        "denial": 3.0, "claim": 2.2, "explanation of benefits": 3.0, "eob": 2.6,
        "not medically necessary": 2.8, "appeal": 2.0, "payer": 1.6,
        "adjudication": 2.0, "remittance": 1.4, "denied": 2.6, "policy number": 1.4,
    },
    "SPAM_OTHER": {
        "limited time offer": 3.4, "act now": 3.0, "unsubscribe": 2.8,
        "special promotion": 2.8, "lowest price": 2.4, "call today": 2.0,
        "no obligation": 2.4, "free quote": 1.6, "toner deal": 2.2,
        "remove from list": 2.6, "conference registration": 1.4, "webinar": 1.6,
        "cruise": 2.4, "vacation": 2.0, "%% off": 1.8, "clearance": 1.6,
    },
}

# Classes the hardened profile adds. Section 13.2 ships none of these, which is
# why v4.1 has no correct destination for most industrial and office traffic.
EXTENDED_LEXICON = {
    "RFQ_QUOTE": {
        "request for quote": 3.4, "rfq": 3.2, "please quote": 3.0,
        "quotation": 2.8, "pricing request": 2.6, "quote request": 3.0,
        "provide pricing": 2.4, "budgetary quote": 2.6, "lead time": 1.4,
        "do not process as an order": 3.0, "this is not an order": 3.2,
    },
    "ORDER_CHANGE": {
        "change order": 3.4, "po revision": 3.2, "revision": 2.0,
        "amend": 2.4, "supersedes": 2.8, "cancel line": 2.6,
        "revised quantity": 2.8, "modification": 2.2, "rev. b": 1.8,
        "previously submitted": 2.0, "amendment": 2.4,
    },
    "INVOICE_REMITTANCE": {
        "invoice": 3.2, "remittance advice": 3.4, "amount due": 2.8,
        "net 30": 2.4, "past due": 2.6, "statement of account": 3.0,
        "please remit": 3.0, "accounts payable": 2.4, "balance forward": 2.6,
    },
    "MRO_WORK_ORDER": {
        "work order": 3.2, "cmms": 2.8, "preventive maintenance": 3.0,
        "corrective maintenance": 3.0, "asset id": 2.4, "downtime": 2.2,
        "equipment failure": 2.8, "breakdown": 2.4, "mro": 2.6,
        "unplanned outage": 2.6, "failure code": 2.4, "line down": 2.8,
    },
    "MILSTRIP_REQUISITION": {
        "milstrip": 3.6, "nsn": 3.0, "national stock number": 3.4,
        "document number": 2.4, "dd form 1348": 3.6, "dd 1348": 3.4,
        "dodaac": 3.0, "priority designator": 3.0, "unit of issue": 2.4,
        "required delivery date": 2.4, "rdd": 2.2, "routing identifier": 2.6,
        "uic": 2.0, "advice code": 2.6, "fund code": 2.4, "signal code": 2.4,
        "nomenclature": 2.2, "force activity designator": 3.0,
        "urgency of need": 2.6, "project code": 2.0, "requisition": 2.2,
    },
    # A DD Form 1155 delivery order carries contract flow-downs and must reach
    # contract administration, not the supply desk that handles a 1348 pull.
    "CONTRACT_DOCUMENT": {
        "service agreement": 3.0, "terms and conditions": 2.4,
        "signature page": 2.8, "executed copy": 2.8, "countersigned": 2.6,
        "master agreement": 2.6, "in witness whereof": 3.0,
        "dd form 1155": 3.6, "dfars": 3.2, "clin": 3.0, "cage code": 2.4,
        "delivery order": 3.2, "contracting officer": 3.0,
        "clauses incorporated": 3.2, "contract number": 2.8,
        "inspection and acceptance": 2.4, "acceptance constitutes": 3.0,
    },
    # Legal and employment records requests share vocabulary with clinical ROI
    # but must never reach the EMR. They need their own class, not a threshold.
    "LEGAL_RECORDS_REQUEST": {
        "subpoena": 3.4, "subpoena duces tecum": 3.6, "law offices": 3.4,
        "attorney": 2.8, "esq": 2.4, "personnel file": 3.2,
        "employment records": 3.4, "pending litigation": 3.0,
        "case no": 2.6, "custodian of records": 2.8, "wage statements": 2.8,
        "performance reviews": 2.6, "disciplinary actions": 2.6,
    },
}


def _fuzzy_present(needle, haystack):
    """Substring match tolerant of one OCR corruption per word.

    Wordpiece tokenisation gives the real model partial robustness to character
    damage; this reproduces that without pretending it is total.
    """
    if needle in haystack:
        return 1.0
    words = needle.split()
    if len(words) == 1:
        if len(needle) < 5:
            return 0.0
        pat = "".join(
            f"{re.escape(c)}?" if i in (len(needle) // 2, len(needle) - 1) else re.escape(c)
            for i, c in enumerate(needle)
        )
        return 0.55 if re.search(pat, haystack) else 0.0
    hits = sum(1 for w in words if len(w) > 3 and w in haystack)
    if hits == len(words):
        return 0.85
    if hits >= max(1, len(words) - 1):
        return 0.5
    return 0.0


def classify(text, profile="baseline", threshold=INTENT_CONFIDENCE_THRESHOLD):
    """Section 13.5 FaxIntentClassifier.classify()."""
    lower = text.lower()
    lexicon = dict(LEXICON)
    if profile == "hardened":
        lexicon.update(EXTENDED_LEXICON)

    scores = {}
    evidence = {}
    for label, terms in lexicon.items():
        total = 0.0
        found = []
        for term, weight in terms.items():
            hit = _fuzzy_present(term, lower)
            if hit:
                total += weight * hit
                found.append((term, round(weight * hit, 2)))
        scores[label] = total
        evidence[label] = sorted(found, key=lambda x: -x[1])[:5]

    # A document with no lexical evidence at all still has to go somewhere; the
    # head's prior leaks probability mass to the majority training class.
    scores["CLARIFICATION_NEEDED"] = 1.15

    # Temperature-scaled softmax over accumulated evidence. T=2.6 reproduces the
    # calibration of the quantised INT8 head reported at 94.2% val accuracy.
    temperature = 2.6
    mx = max(scores.values())
    exps = {k: math.exp((v - mx) / temperature) for k, v in scores.items()}
    denom = sum(exps.values())
    probs = {k: v / denom for k, v in exps.items()}

    predicted = max(probs, key=probs.get)
    confidence = probs[predicted]

    result = {
        "scores": {k: round(v, 2) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
        "probabilities": {k: round(v, 4) for k, v in sorted(probs.items(), key=lambda x: -x[1])[:4]},
        "evidence": {k: v for k, v in evidence.items() if v},
    }

    if confidence < threshold:
        result.update({
            "intent": "CLARIFICATION_NEEDED",
            "original_intent": predicted,
            "confidence": round(confidence, 4),
            "requires_review": True,
            "review_rule": f"confidence {confidence:.3f} < threshold {threshold:.2f}",
        })
    else:
        result.update({
            "intent": predicted,
            "confidence": round(confidence, 4),
            "requires_review": predicted == "CLARIFICATION_NEEDED",
        })
    return result


# --- Section 13.4 NER ------------------------------------------------------
# Patterns are written against post-OCR text, so they carry the same brittleness
# the shipped extractor has: a corrupted delimiter loses the whole entity.

# `H` is horizontal whitespace only. Label/value pairs on a fax form never span
# a line break, and a pattern that lets them cross one will happily swallow the
# next field's label into the captured value.
H = r"[^\S\n]"

ENTITY_PATTERNS = {
    "PATIENT_NAME": [
        rf"(?:patient|patient name|pt\.?){H}*[:#]{H}*([A-Z][A-Za-z'\-]+(?:{H}+[A-Z][A-Za-z'\-]+){{0,2}})",
        rf"(?:name of (?:patient|employee)){H}*[:#]{H}*([A-Z][A-Za-z'\-]+(?:{H}+[A-Z][A-Za-z'\-]+){{0,2}})",
    ],
    "DATE_OF_BIRTH": [
        rf"(?:dob|d\.o\.b\.?|date of birth){H}*[:#]?{H}*(\d{{1,2}}[/\-]\d{{1,2}}[/\-]\d{{2,4}})",
    ],
    "MRN": [
        rf"(?:mrn|medical record (?:number|no\.?)|record{H}*#){H}*[:#]?{H}*([A-Z0-9\-]{{5,12}})",
    ],
    "PART_NUMBER": [
        rf"(?:part{H}*(?:number|no\.?|#)|p/n|item{H}*(?:number|no\.?|#)|nsn|numero de parte){H}*[:#]?{H}*([A-Z0-9][A-Z0-9\-/\.]{{3,20}})",
    ],
    "QUANTITY": [
        rf"(?:quantity|qty|cantidad){H}*[:#]?{H}*(\d{{1,6}}(?:{H}*(?:ea|each|units?|pcs?|pz|cs|box|rolls?))?)",
        rf"\b(\d{{1,5}}){H}+(?:ea|each|units?|pcs)\b",
    ],
    "PO_NUMBER": [
        rf"(?:p\.?o\.?{H}*(?:number|no\.?|#)?|purchase order{H}*(?:number|no\.?|#)?|numero de orden){H}*[:#]?{H}*([A-Z0-9][A-Z0-9\-/]{{4,20}})",
    ],
    "FAX_NUMBER": [
        rf"(?:fax(?:{H}*(?:back|to|number|no\.?|#))?|reply fax|confirm(?:ation)? to){H}*[:#]?{H}*(\+?1?[ \t\-\.]?\(?\d{{3}}\)?[ \t\-\.]?\d{{3}}[ \t\-\.]?\d{{4}})",
    ],
    "FACILITY_NAME": [
        rf"(?:from|facility|company|organization|activity){H}*[:#]{H}*([A-Z][A-Za-z0-9&'\.\- ]{{4,42}})",
    ],
}

# Industrial / defence entities. Not in section 13.4; the hardened profile needs
# them because a MILSTRIP line has no "part number:" label to anchor on.
EXTENDED_ENTITY_PATTERNS = {
    "NSN": [r"\b(\d{4}[\-\s]?\d{2}[\-\s]?\d{3}[\-\s]?\d{4})\b"],
    "CAGE_CODE": [rf"(?:cage(?:{H}*code)?){H}*[:#]?{H}*([0-9A-Z]{{5}})"],
    "DODAAC": [rf"(?:dodaac|doda{{2}}c|activity code){H}*[:#]?{H}*([A-Z0-9]{{6}})"],
    "WORK_ORDER": [rf"(?:work order|w\.o\.){H}*[:#]?{H}*([A-Z0-9][A-Z0-9\-]{{3,16}})"],
    "ASSET_ID": [rf"(?:asset(?:{H}*id)?|equipment(?:{H}*id)?){H}*[:#]{H}*([A-Z0-9][A-Z0-9\-]{{2,16}})"],
    "CONTRACT_NUMBER": [r"\b([A-Z0-9]{6}-\d{2}-[A-Z]-\d{4})\b"],
    "INVOICE_NUMBER": [rf"(?:invoice{H}*(?:number|no\.?|#)){H}*[:#]?{H}*([A-Z0-9][A-Z0-9\-]{{3,18}})"],
    "PRIORITY_DESIGNATOR": [rf"(?:priority(?:{H}*designator)?){H}*[:#]?{H}*(\d{{2}})\b"],
}


def extract_entities(text, confidences=None, profile="baseline"):
    """Section 13.4 entity extraction. Returns {type: {value, confidence}}."""
    patterns = dict(ENTITY_PATTERNS)
    if profile == "hardened":
        patterns.update(EXTENDED_ENTITY_PATTERNS)

    conf_map = {}
    if confidences:
        for tok, c in confidences:
            conf_map.setdefault(tok.strip(".,:;#"), c)

    found = {}
    for etype, pats in patterns.items():
        for pat in pats:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                value = m.group(1).strip().rstrip(".,;")
                # An entity is only as trustworthy as the weakest token in it.
                toks = [t.strip(".,:;#") for t in value.split()]
                confs = [conf_map[t] for t in toks if t in conf_map]
                found[etype] = {
                    "value": value,
                    "confidence": round(min(confs), 3) if confs else None,
                }
                break
    return found
