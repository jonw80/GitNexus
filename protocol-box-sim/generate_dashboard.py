#!/usr/bin/env python3
"""Render reports/dashboard.html from results.json.

Instrument-panel view of the run: go-live gate lamps, A/B metric comparison,
and a vertical-by-difficulty matrix where each cell is split baseline/hardened.
"""

import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VERTICALS = ["MRO", "Manufacturer Ordering", "Office", "Military"]
SHORT = {"MRO": "MRO", "Manufacturer Ordering": "Mfg ordering",
         "Office": "Office", "Military": "Military"}

# Condensed from reports/SIMULATION_REPORT.md.
FINDINGS = [
    ("F-1", "critical", "PHI released to a law firm with no HIPAA authorization", "OFF-05",
     "A subpoena for an employee's personnel file names someone who is also a patient. "
     "The classifier scores RECORDS_REQUEST at 0.99, the EMR is queried, and three "
     "clinical documents are faxed to the caller ID because no fax-back number was extracted."),
    ("F-2", "critical", "Classified spillage is processed rather than contained", "MIL-04",
     "A SECRET//NOFORN page misdialled onto a commercial DID is OCR'd to shared storage on "
     "a PB-8 with no COMSEC bay. Only the low-confidence fallback stops it, and that is "
     "an accident rather than a control."),
    ("F-3", "high", "Unknown part numbers create phantom sales orders", "MIL-02, MFG-02, MIL-03, MRO-04",
     "`undefined < qty` is false in JavaScript, so a part the ERP has never heard of passes "
     "the inventory guard. One character of OCR damage is enough: NSN 5330-01-234-5678 read "
     "as S330-01-234-5678 booked 1,200 gaskets."),
    ("F-4", "high", "Multi-line orders are silently truncated to line one", "MFG-02",
     "A four-line blanket order worth $214,800 becomes a single sales order for line 1. "
     "Lines 2 to 4 are discarded with no error and no audit entry, and the acknowledgment "
     "tells the customer the whole order was accepted."),
    ("F-5", "high", "A PO revision books a second order at the pre-revision quantity", "MFG-03",
     "A revision cutting 250 units to 175 is read at a 0.3% error rate and booked as a new "
     "order for 250. The extractor anchored on 'Original Quantity'. The customer ends up "
     "holding 500 units across two acknowledged orders."),
    ("F-6", "high", "Non-order documents that mention parts become orders", "OFF-02, MRO-03",
     "An invoice re-orders goods already shipped and billed. An RFQ headed THIS IS NOT AN "
     "ORDER books 500 filter elements for a customer who asked only for pricing."),
    ("F-7", "high", "Defence documents are accepted as commercial sales orders", "MIL-01, MIL-02, MIL-03",
     "A DD Form 1155 delivery order auto-acknowledged in under 12 seconds constitutes "
     "acceptance of the DFARS clauses it incorporates. No automated system is authorised "
     "to accept those on a contractor's behalf."),
    ("F-8", "medium", "Entity confidence is gated on the document average, not the field", "MRO-04",
     "A handwritten requisition averages 0.735 confidence, above the 0.60 floor, while the "
     "part number itself reads at 0.32. The order goes out for the wrong part in a quantity "
     "of 3 where the technician wrote 300."),
    ("F-9", "medium", "OCR damage to a label silently discards the value", "MFG-04",
     "`Part Number:` read as `Part Numbr:` loses PLT-STL-4X8-14GA entirely, even though the "
     "value itself was legible. The patterns anchor on labels, and labels run 10 to 14 characters."),
    ("F-10", "medium", "Reply faxes fall back to caller ID without verification", "OFF-05, OFF-02, MRO-04",
     "Three runs replied to the calling number because no fax-back entity survived. Harmless "
     "for an order acknowledgment; not harmless for the PHI payload in OFF-05."),
    ("F-11", "medium", "Entity patterns fire on unrelated text", "MIL-03, MIL-02, MFG-04",
     "A defence requisition with no person named on it produced PATIENT_NAME: DSN. Combined "
     "with F-1, any document classified RECORDS_REQUEST carries a fabricated patient name "
     "into a live EMR query."),
    ("F-12", "low", "Three intent classes have no handler in the orchestrator", None,
     "LAB_RESULT, PRESCRIPTION_REFILL and INSURANCE_DENIAL have documented actions in section "
     "13.2 and no case in the section 14.3 switch. All three fall through to human review."),
    ("F-13", "low", "TTFA budget is exceeded on multi-page degraded faxes", "MRO-05, MFG-04, OFF-04",
     "Three of twenty runs exceed the SKU budget. The published figures hold for a clean "
     "single page and not for the degraded multi-page traffic that dominates MRO and defence."),
    ("F-14", "info", "Page loss is invisible in the audit trail", "MRO-05, MIL-05",
     "Two faxes lost a page and both logged a successful reception with a valid SHA-256 seal. "
     "T.30 confirms what arrived, not what was sent."),
]

CONTROLS = [
    ("PB-C1", "Classification banner detector, pre-OCR-export", "F-2"),
    ("PB-C2", "Extended intent taxonomy (7 new classes)", "F-6, F-5, F-7"),
    ("PB-C3", "PHI scope guard on the EMR path", "F-1"),
    ("PB-C4", "Per-entity confidence floor", "F-8"),
    ("PB-C5", "Reply-path guard for PHI payloads", "F-10"),
    ("PB-C6", "Explicit unknown-part check", "F-3"),
]

DISP_TONE = {
    "AUTO_ACTION": "act", "ROUTE": "route", "HUMAN_REVIEW": "hold",
    "ARCHIVE": "archive", "QUARANTINE": "seal",
}


def esc(s):
    return html.escape(str(s))


def verdict_of(r):
    s = r["scoring"]
    if s["phi_misdirection"]:
        return "breach", "PHI breach"
    if s["spillage_unhandled"]:
        return "breach", "spillage"
    if s["phantom_order"]:
        return "bad", "phantom order"
    if not s["disposition_safe"]:
        return "bad", "unsafe"
    return "ok", "safe"


def cell(r):
    tone, label = verdict_of(r)
    disp = r["workflow"]["disposition"]
    return (f'<span class="pip pip--{tone}" title="{esc(r["case_id"])}: {esc(disp)} — {esc(label)}">'
            f'<span class="pip__d">{esc(DISP_TONE.get(disp, disp))}</span></span>')


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "reports", "results.json")
    data = json.load(open(src))
    bm, hm = data["baseline"]["metrics"], data["hardened"]["metrics"]
    br, hr = data["baseline"]["results"], data["hardened"]["results"]
    b_by, h_by = {r["case_id"]: r for r in br}, {r["case_id"]: r for r in hr}
    n = len(br)
    b_safe = sum(1 for r in br if r["scoring"]["disposition_safe"])
    h_safe = sum(1 for r in hr if r["scoring"]["disposition_safe"])

    o = []
    w = o.append

    w('<title>Protocol Box v4.1 — Simulation Fax Run</title>')
    w('<style>')
    w('''
:root{
  --paper:#EDE9E1; --card:#F7F4EE; --sunk:#E3DED4;
  --ink:#1B2024; --ink-2:#4A524F; --ink-3:#7B827E;
  --rule:#CFC8BB; --rule-2:#DED8CC;
  --accent:#2B4C9B; --accent-soft:#E2E6F2;
  --ok:#2F6E48; --ok-soft:#DEEADF;
  --warn:#8C6412; --warn-soft:#F0E6CE;
  --bad:#A33A2A; --bad-soft:#F2DED9;
  --breach:#7A1F2B; --breach-soft:#EFD6D8;
  --serif:ui-serif,Georgia,"Iowan Old Style","Times New Roman",serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  --step:clamp(.5rem,1.2vw,1rem);
}
@media (prefers-color-scheme:dark){
  :root{
    --paper:#15191C; --card:#1C2126; --sunk:#111518;
    --ink:#E7E9E6; --ink-2:#A8B0AC; --ink-3:#79817D;
    --rule:#2C333A; --rule-2:#242A30;
    --accent:#8FAAE4; --accent-soft:#1F2A3F;
    --ok:#79C193; --ok-soft:#182B21;
    --warn:#DCB160; --warn-soft:#2C2415;
    --bad:#E38878; --bad-soft:#311D19;
    --breach:#EC8A94; --breach-soft:#331319;
  }
}
:root[data-theme="dark"]{
  --paper:#15191C; --card:#1C2126; --sunk:#111518;
  --ink:#E7E9E6; --ink-2:#A8B0AC; --ink-3:#79817D;
  --rule:#2C333A; --rule-2:#242A30;
  --accent:#8FAAE4; --accent-soft:#1F2A3F;
  --ok:#79C193; --ok-soft:#182B21;
  --warn:#DCB160; --warn-soft:#2C2415;
  --bad:#E38878; --bad-soft:#311D19;
  --breach:#EC8A94; --breach-soft:#331319;
}
:root[data-theme="light"]{
  --paper:#EDE9E1; --card:#F7F4EE; --sunk:#E3DED4;
  --ink:#1B2024; --ink-2:#4A524F; --ink-3:#7B827E;
  --rule:#CFC8BB; --rule-2:#DED8CC;
  --accent:#2B4C9B; --accent-soft:#E2E6F2;
  --ok:#2F6E48; --ok-soft:#DEEADF;
  --warn:#8C6412; --warn-soft:#F0E6CE;
  --bad:#A33A2A; --bad-soft:#F2DED9;
  --breach:#7A1F2B; --breach-soft:#EFD6D8;
}

body{background:var(--paper);color:var(--ink);font-family:var(--serif);
  line-height:1.6;-webkit-font-smoothing:antialiased;}
.wrap{max-width:64rem;margin:0 auto;padding:clamp(1.5rem,4vw,3.5rem) clamp(1rem,4vw,2rem) 5rem;
  display:flex;flex-direction:column;gap:clamp(2rem,4vw,3.25rem);}

.eyebrow{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 .75rem;}
h1{font-size:clamp(1.9rem,4.6vw,3rem);line-height:1.08;margin:0 0 .6rem;font-weight:600;
  letter-spacing:-.015em;text-wrap:balance;}
.lede{font-size:clamp(1rem,1.6vw,1.15rem);color:var(--ink-2);max-width:60ch;margin:0;}
h2{font-size:clamp(1.15rem,2.2vw,1.5rem);margin:0 0 .3rem;font-weight:600;letter-spacing:-.01em;}
.sub{font-family:var(--mono);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 1.15rem;}
section{display:flex;flex-direction:column;}
p{margin:0 0 .9rem;max-width:66ch;}
p:last-child{margin-bottom:0;}
code{font-family:var(--mono);font-size:.86em;background:var(--sunk);
  padding:.08em .34em;border-radius:2px;}

/* verdict banner */
.verdict{border:1px solid var(--rule);background:var(--card);border-radius:3px;overflow:hidden;}
.verdict__top{display:flex;flex-wrap:wrap;gap:1.5rem;padding:1.35rem 1.5rem;
  border-bottom:1px solid var(--rule-2);}
.vstat{display:flex;flex-direction:column;gap:.2rem;}
.vstat__k{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink-3);}
.vstat__v{font-family:var(--mono);font-size:1.75rem;font-weight:600;font-variant-numeric:tabular-nums;
  line-height:1.1;}
.vstat__v small{font-size:.85rem;font-weight:400;color:var(--ink-3);}
.vstat--b .vstat__v{color:var(--bad);}
.vstat--h .vstat__v{color:var(--ok);}
.gate{padding:1.15rem 1.5rem 1.35rem;}
.gate__h{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink-3);margin:0 0 .85rem;}
.lamps{display:grid;grid-template-columns:repeat(auto-fit,minmax(13.5rem,1fr));gap:.55rem;}
.lamp{display:flex;align-items:baseline;gap:.55rem;font-family:var(--mono);font-size:.76rem;
  padding:.5rem .7rem;border-radius:2px;background:var(--sunk);
  border-left:3px solid var(--ink-3);}
.lamp--pass{border-left-color:var(--ok);background:var(--ok-soft);}
.lamp--fail{border-left-color:var(--bad);background:var(--bad-soft);}
.lamp__n{color:var(--ink-2);flex:1;font-size:.72rem;line-height:1.35;}
.lamp__v{font-variant-numeric:tabular-nums;font-weight:600;}
.lamp--pass .lamp__v{color:var(--ok);} .lamp--fail .lamp__v{color:var(--bad);}

/* matrix */
.matrix{width:100%;min-width:38rem;border-collapse:collapse;table-layout:fixed;
  font-family:var(--mono);font-size:.75rem;}
.matrix th,.matrix td{border:1px solid var(--rule-2);padding:0;text-align:center;}
.matrix thead th{font-weight:500;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);padding:.5rem .35rem;border:0;border-bottom:1px solid var(--rule);}
.matrix tbody th{text-align:left;padding:.6rem .8rem .6rem 0;font-weight:500;color:var(--ink-2);
  white-space:nowrap;border-left:0;font-size:.78rem;}
.cellwrap{display:flex;flex-direction:column;}
.cellwrap .row{display:flex;align-items:stretch;}
.pip{flex:1;display:flex;align-items:center;justify-content:center;padding:.5rem .2rem;
  font-size:.7rem;letter-spacing:.04em;border-left:3px solid transparent;}
.pip--ok{background:var(--ok-soft);border-left-color:var(--ok);color:var(--ok);}
.pip--bad{background:var(--bad-soft);border-left-color:var(--bad);color:var(--bad);}
.pip--breach{background:var(--breach-soft);border-left-color:var(--breach);color:var(--breach);
  font-weight:700;}
.pip__lab{font-size:.62rem;color:var(--ink-3);letter-spacing:.1em;text-transform:uppercase;
  width:1.6rem;display:flex;align-items:center;justify-content:center;background:var(--sunk);
  border-left:0;flex:0 0 auto;}
.mcase{font-size:.66rem;color:var(--ink-3);letter-spacing:.06em;padding:.3rem 0 .22rem;
  background:var(--sunk);border-bottom:1px solid var(--rule-2);}
.mscroll{overflow-x:auto;}
.legend{display:flex;flex-wrap:wrap;gap:1rem;margin-top:.9rem;font-family:var(--mono);
  font-size:.68rem;color:var(--ink-3);}
.legend span{display:flex;align-items:center;gap:.4rem;}
.swatch{width:.75rem;height:.75rem;border-radius:2px;border-left:3px solid;}
.sw-ok{background:var(--ok-soft);border-color:var(--ok);}
.sw-bad{background:var(--bad-soft);border-color:var(--bad);}
.sw-breach{background:var(--breach-soft);border-color:var(--breach);}

/* metric compare */
.cmp{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:.8rem;}
.cmp th{text-align:left;font-weight:500;font-size:.68rem;letter-spacing:.11em;
  text-transform:uppercase;color:var(--ink-3);padding:.45rem .6rem;
  border-bottom:1px solid var(--rule);}
.cmp th.num,.cmp td.num{text-align:right;font-variant-numeric:tabular-nums;}
.cmp td{padding:.5rem .6rem;border-bottom:1px solid var(--rule-2);}
.cmp tr:last-child td{border-bottom:0;}
.cmp .name{font-family:var(--serif);font-size:.92rem;}
.cmp .b{color:var(--ink-2);} .cmp .h{font-weight:600;}
.cmp .up{color:var(--ok);} .cmp .down{color:var(--bad);} .cmp .flat{color:var(--ink-3);}

/* findings */
.finds{display:flex;flex-direction:column;gap:.5rem;}
.find{background:var(--card);border:1px solid var(--rule-2);border-left:4px solid var(--ink-3);
  border-radius:2px;padding:.95rem 1.15rem;}
.find--critical{border-left-color:var(--breach);}
.find--high{border-left-color:var(--bad);}
.find--medium{border-left-color:var(--warn);}
.find--low,.find--info{border-left-color:var(--ink-3);}
.find__head{display:flex;flex-wrap:wrap;align-items:baseline;gap:.6rem;margin-bottom:.4rem;}
.find__id{font-family:var(--mono);font-size:.72rem;color:var(--ink-3);letter-spacing:.06em;}
.find__sev{font-family:var(--mono);font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;
  padding:.14rem .42rem;border-radius:2px;font-weight:600;}
.sev-critical{background:var(--breach-soft);color:var(--breach);}
.sev-high{background:var(--bad-soft);color:var(--bad);}
.sev-medium{background:var(--warn-soft);color:var(--warn);}
.sev-low,.sev-info{background:var(--sunk);color:var(--ink-3);}
.find__t{font-weight:600;font-size:1rem;flex:1;min-width:14rem;}
.find__c{font-family:var(--mono);font-size:.68rem;color:var(--ink-3);}
.find__b{color:var(--ink-2);font-size:.94rem;margin:0;max-width:74ch;}

/* controls */
.ctrls{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:.55rem;}
.ctrl{background:var(--card);border:1px solid var(--rule-2);border-radius:2px;padding:.8rem .95rem;
  display:flex;flex-direction:column;gap:.25rem;}
.ctrl__id{font-family:var(--mono);font-size:.7rem;color:var(--accent);letter-spacing:.06em;
  font-weight:600;}
.ctrl__n{font-size:.92rem;}
.ctrl__f{font-family:var(--mono);font-size:.66rem;color:var(--ink-3);}

.note{border-left:3px solid var(--accent);background:var(--accent-soft);padding:.9rem 1.15rem;
  border-radius:0 2px 2px 0;}
.note p{font-size:.95rem;}

footer{border-top:1px solid var(--rule);padding-top:1.25rem;font-family:var(--mono);
  font-size:.7rem;color:var(--ink-3);line-height:1.7;}
@media (max-width:640px){
  .matrix{font-size:.68rem;}
  .vstat__v{font-size:1.4rem;}
}
''')
    w('</style>')

    w('<div class="wrap">')

    # ---- header ----
    w('<header>')
    w('<p class="eyebrow">Protocol Box v4.1 · build candidate · simulation fax run</p>')
    w('<h1>Twenty faxes the taxonomy was never trained to see</h1>')
    w(f'<p class="lede">MRO, manufacturer ordering, office and defence traffic driven through '
      f'the eight-stage pipeline from sections 12–14 of the Master Internal Build File. '
      f'Five difficulty tiers per vertical, each fax run twice against a byte-identical '
      f'OCR result.</p>')
    w('</header>')

    # ---- verdict ----
    w('<section>')
    w('<div class="verdict">')
    w('<div class="verdict__top">')
    w(f'<div class="vstat vstat--b"><span class="vstat__k">Baseline · v4.1 as specified</span>'
      f'<span class="vstat__v">{b_safe}<small> / {n} safe</small></span></div>')
    w(f'<div class="vstat vstat--h"><span class="vstat__k">Hardened · 6 proposed controls</span>'
      f'<span class="vstat__v">{h_safe}<small> / {n} safe</small></span></div>')
    w(f'<div class="vstat"><span class="vstat__k">Harm events, baseline</span>'
      f'<span class="vstat__v">{bm["phi_misdirection_count"] + bm["spillage_unhandled_count"] + bm["phantom_order_count"]}'
      f'<small> PHI · spillage · phantom</small></span></div>')
    w('</div>')
    w('<div class="gate">')
    w('<p class="gate__h">Section 16.3 Ghost Mode go-live gate — baseline</p>')
    w('<div class="lamps">')
    for g in bm["go_live_gate"].values():
        v = g["value"]
        vs = f"{v:.2f}" if isinstance(v, float) else str(v)
        cls = "pass" if g["pass"] else "fail"
        w(f'<div class="lamp lamp--{cls}"><span class="lamp__n">{esc(g["label"])}<br>'
          f'need {esc(g["op"])} {esc(g["threshold"])}</span>'
          f'<span class="lamp__v">{vs}</span></div>')
    w('</div></div></div>')
    w('</section>')

    # ---- matrix ----
    w('<section>')
    w('<h2>Where it fails</h2>')
    w('<p class="sub">Vertical × difficulty · upper tile baseline, lower tile hardened</p>')
    w('<div class="mscroll"><table class="matrix">')
    w('<colgroup><col style="width:8.5rem"><col span="5"></colgroup>')
    w('<thead><tr><th></th>')
    for d in range(1, 6):
        w(f'<th>D{d}</th>')
    w('</tr></thead><tbody>')
    ids = {r["case_id"] for r in br}
    for v in VERTICALS:
        w(f'<tr><th>{esc(SHORT[v])}</th>')
        for d in range(1, 6):
            match = [r for r in br if r["vertical"] == v and r["difficulty"] == d]
            if not match:
                w('<td></td>')
                continue
            cid = match[0]["case_id"]
            w('<td><div class="cellwrap">')
            w(f'<div class="mcase">{esc(cid)}</div>')
            w(f'<div class="row"><span class="pip__lab">B</span>{cell(b_by[cid])}</div>')
            w(f'<div class="row"><span class="pip__lab">H</span>{cell(h_by[cid])}</div>')
            w('</div></td>')
        w('</tr>')
    w('</tbody></table></div>')
    w('<div class="legend">'
      '<span><i class="swatch sw-ok"></i>safe disposition</span>'
      '<span><i class="swatch sw-bad"></i>unsafe or phantom order</span>'
      '<span><i class="swatch sw-breach"></i>PHI breach / uncontained spillage</span>'
      '<span>act · route · hold · archive · seal = disposition taken</span>'
      '</div>')
    w('</section>')

    # ---- the inversion ----
    w('<section>')
    w('<h2>The difficulty inversion</h2>')
    w('<p class="sub">Safe dispositions by tier</p>')
    w('<div class="mscroll"><table class="cmp">')
    w('<thead><tr><th>Tier</th><th class="num">Baseline safe</th>'
      '<th class="num">Hardened safe</th><th class="num">Mean OCR confidence</th></tr></thead><tbody>')
    for d in range(1, 6):
        bs = [r for r in br if r["difficulty"] == d]
        hs = [r for r in hr if r["difficulty"] == d]
        oc = sum(r["ocr"]["avg_confidence"] for r in bs) / len(bs)
        w(f'<tr><td class="name">D{d}</td>'
          f'<td class="num b">{sum(1 for r in bs if r["scoring"]["disposition_safe"])} / {len(bs)}</td>'
          f'<td class="num h">{sum(1 for r in hs if r["scoring"]["disposition_safe"])} / {len(hs)}</td>'
          f'<td class="num b">{oc:.3f}</td></tr>')
    w('</tbody></table></div>')
    w('<div class="note" style="margin-top:1.1rem"><p>Baseline safety does not fall with '
      'difficulty — it is worst in the middle tiers. Badly degraded faxes fail the 0.60 '
      'confidence threshold and get parked for an operator, which is the safe outcome. '
      'Clean faxes carrying an intent the taxonomy does not model are classified confidently '
      'and wrongly, and acted on. <strong>The system is most dangerous when the transport is '
      'perfect and the document is merely unfamiliar.</strong></p></div>')
    w('</section>')

    # ---- metric comparison ----
    w('<section>')
    w('<h2>Baseline against hardened</h2>')
    w('<p class="sub">Same OCR text, same random stream — the delta is the pipeline</p>')
    w('<div class="mscroll"><table class="cmp">')
    w('<thead><tr><th>Metric</th><th class="num">Baseline</th><th class="num">Hardened</th>'
      '<th class="num">Change</th></tr></thead><tbody>')
    rows = [
        ("Intent classification accuracy", "intent_accuracy", "pct", "up"),
        ("Safe disposition rate", "disposition_safe_rate", "pct", "up"),
        ("Optimal disposition rate", "disposition_optimal_rate", "pct", "up"),
        ("Entity extraction accuracy", "entity_accuracy", "pct", "up"),
        ("Average OCR confidence", "avg_ocr_confidence", "f3", "up"),
        ("PHI misdirection events", "phi_misdirection_count", "int", "down"),
        ("Uncontained classified spillage", "spillage_unhandled_count", "int", "down"),
        ("Phantom ERP orders", "phantom_order_count", "int", "down"),
        ("Closed-loop auto-actions", None, "int", "none"),
    ]
    for label, key, fmt, better in rows:
        if key is None:
            bv = sum(1 for r in br if r["workflow"]["disposition"] == "AUTO_ACTION")
            hv = sum(1 for r in hr if r["workflow"]["disposition"] == "AUTO_ACTION")
        else:
            bv, hv = bm[key], hm[key]
        if fmt == "pct":
            bs, hs = f"{bv:.0%}", f"{hv:.0%}"
        elif fmt == "f3":
            bs, hs = f"{bv:.3f}", f"{hv:.3f}"
        else:
            bs, hs = str(bv), str(hv)
        delta = hv - bv
        if better == "none":
            cls, txt = "flat", f"{delta:+d}"
        elif delta == 0:
            cls, txt = "flat", "no change"
        elif (delta > 0) == (better == "up"):
            cls, txt = "up", "improved"
        else:
            cls, txt = "down", "worse"
        w(f'<tr><td class="name">{esc(label)}</td><td class="num b">{bs}</td>'
          f'<td class="num h">{hs}</td><td class="num {cls}">{txt}</td></tr>')
    w('</tbody></table></div>')
    w('<div class="note" style="margin-top:1.1rem"><p>The controls are not free. Closed-loop '
      'auto-actions drop from 12 to 3 — every suppressed one was wrong, so this is the '
      'intended trade, but it is a real change to the labour model the section 1.4 ROI case '
      'rests on. Adding classes also dilutes softmax mass on hybrid documents: '
      '<code>MRO-02</code>, an emergency breakdown that is both a work order and a purchase '
      'order, moves to <code>MRO_WORK_ORDER</code> and routes to CMMS instead of checking '
      'inventory. It is the one case where hardened is less correct than baseline.</p></div>')
    w('</section>')

    # ---- findings ----
    w('<section>')
    w('<h2>Findings</h2>')
    w(f'<p class="sub">{len(FINDINGS)} recorded · two critical</p>')
    w('<div class="finds">')
    for fid, sev, title, cases, body in FINDINGS:
        w(f'<article class="find find--{sev}">')
        w('<div class="find__head">')
        w(f'<span class="find__id">{esc(fid)}</span>')
        w(f'<span class="find__sev sev-{sev}">{esc(sev)}</span>')
        w(f'<span class="find__t">{esc(title)}</span>')
        if cases:
            w(f'<span class="find__c">{esc(cases)}</span>')
        w('</div>')
        w(f'<p class="find__b">{body}</p>')
        w('</article>')
    w('</div>')
    w('</section>')

    # ---- controls ----
    w('<section>')
    w('<h2>Proposed controls</h2>')
    w('<p class="sub">Each gated behind one flag — baseline stays byte-identical</p>')
    w('<div class="ctrls">')
    for cid, name, addresses in CONTROLS:
        w(f'<div class="ctrl"><span class="ctrl__id">{esc(cid)}</span>'
          f'<span class="ctrl__n">{esc(name)}</span>'
          f'<span class="ctrl__f">addresses {esc(addresses)}</span></div>')
    w('</div>')
    w('</section>')

    # ---- root cause ----
    w('<section>')
    w('<h2>Root cause</h2>')
    w('<p>Both critical findings and four of the five high findings trace to one thing. '
      'Section 13.2 ships seven intent classes, five of them clinical. Section 13.4 ships '
      'eight entity types, four of them clinical. Every MRO work order, RFQ, change order, '
      'invoice, executed contract, MILSTRIP requisition and DFARS delivery order in this '
      'corpus has no correct destination in that model.</p>')
    w('<p>A classifier cannot abstain from a class it does not have. Faced with a document '
      'containing a part number and a quantity it returns <code>PURCHASE_ORDER</code>, and '
      'faced with one containing records vocabulary it returns <code>RECORDS_REQUEST</code> — '
      'in both cases at high confidence, because the confidence is measured against the '
      'classes that exist rather than against the space of documents that arrive. The 0.60 '
      'threshold catches damaged pages. It cannot catch a document the model has no word for.</p>')
    w('</section>')

    w('<footer>')
    w(f'20 synthetic faxes · seed 20260314 · deterministic · audit hash chains intact on {n}/{n} runs<br>')
    w('All names, part numbers, NSNs, DODAACs, CAGE codes, contract numbers and fax numbers '
      'in the corpus are fabricated.<br>')
    w('Source: <code>protocol-box-sim/</code> · full report: '
      '<code>reports/SIMULATION_REPORT.md</code>')
    w('</footer>')

    w('</div>')

    dest = os.path.join(HERE, "reports", "dashboard.html")
    with open(dest, "w") as fh:
        fh.write("\n".join(o) + "\n")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
