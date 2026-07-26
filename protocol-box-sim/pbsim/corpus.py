"""Simulation fax corpus: 4 verticals x 5 difficulty tiers.

Difficulty is a composite of transport quality (line, DPI, skew, fade, page
loss), document structure (forms, handwriting, multi-page, multi-line), and
semantic distance from the v4.1 training distribution.

  D1  clean transport, in-taxonomy intent, single action
  D2  clean-ish transport, in-taxonomy intent, branch logic (inventory, urgency)
  D3  clean transport, intent outside the shipped taxonomy
  D4  degraded transport or handwriting, plus taxonomy or safety pressure
  D5  compound failure: degraded transport AND structure AND taxonomy

`\f` marks a page boundary. `[[hw]]...[[/hw]]` marks handwritten regions, which
the OCR model degrades at ~6.5x the machine-print error rate.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FaxCase:
    case_id: str
    vertical: str
    difficulty: int
    title: str
    sku: str
    did: str
    did_class: str            # clinical | industrial | office | defense
    caller_id: str
    line_quality: float
    pages: int
    is_form: bool
    source_quality: Dict
    raw_text: str
    true_type: str            # descriptive ground truth
    expected_intent: str      # correct label within the v4.1 7-class taxonomy
    optimal_disposition: str
    safe_dispositions: List[str]
    required_entities: Dict[str, str] = field(default_factory=dict)
    hazard: Optional[str] = None
    notes: str = ""
    # Correct label once the proposed classes exist. Defaults to the v4.1 label.
    expected_intent_hardened: Optional[str] = None

    def expected_for(self, profile):
        if profile == "hardened" and self.expected_intent_hardened:
            return self.expected_intent_hardened
        return self.expected_intent


def _sq(dpi=200, skew=0.2, noise=0.03, fade=0.0, page_loss=0, second_gen=False):
    return {
        "dpi": dpi, "skew_deg": skew, "noise": noise,
        "thermal_fade": fade, "page_loss": page_loss,
        "second_generation": second_gen,
    }


CASES: List[FaxCase] = []


# ===========================================================================
# MRO - Maintenance, Repair & Operations
# ===========================================================================

CASES.append(FaxCase(
    case_id="MRO-01", vertical="MRO", difficulty=1,
    title="Routine MRO stores replenishment order",
    sku="PB-8", did="+15550301", did_class="industrial", caller_id="+13175550142",
    line_quality=0.95, pages=1, is_form=False, source_quality=_sq(),
    true_type="Purchase order (MRO consumables)",
    expected_intent="PURCHASE_ORDER", optimal_disposition="AUTO_ACTION",
    safe_dispositions=["AUTO_ACTION", "HUMAN_REVIEW"],
    required_entities={"PART_NUMBER": "BRG-6205-2RS", "QUANTITY": "120",
                       "PO_NUMBER": "PO-2026-11884", "FAX_NUMBER": "317-555-0143"},
    notes="Baseline happy path. Clean typed order, in stock, explicit fax-back.",
    raw_text="""MERIDIAN FOODS - PLANT 2 MAINTENANCE STORES
4400 W Industrial Pkwy, Indianapolis IN 46241

PURCHASE ORDER

From: Meridian Foods Plant 2 Maintenance
P.O. Number: PO-2026-11884
Date: 03/11/2026
Buyer: R. Castellano, Maintenance Planner

To: Apex Industrial Supply
Attn: Inside Sales

Part Number: BRG-6205-2RS
Description: Deep groove ball bearing, 25mm bore, double sealed
Quantity: 120 EA
Unit Price: $4.18
Line Total: $501.60

Ship To: Meridian Foods Plant 2, Receiving Dock C
Delivery Date: 03/25/2026
Terms: Net 30

Please confirm receipt and acknowledge this order.
Fax back: 317-555-0143

R. Castellano
Maintenance Planner
"""))

CASES.append(FaxCase(
    case_id="MRO-02", vertical="MRO", difficulty=2,
    title="Emergency breakdown expedite - quantity exceeds stock",
    sku="PB-8", did="+15550301", did_class="industrial", caller_id="+16145550188",
    line_quality=0.88, pages=1, is_form=False, source_quality=_sq(noise=0.06, skew=0.9),
    true_type="Purchase order (emergency expedite)",
    expected_intent="PURCHASE_ORDER", optimal_disposition="HUMAN_REVIEW",
    safe_dispositions=["HUMAN_REVIEW"],
    required_entities={"PART_NUMBER": "HYD-SEAL-K4471", "QUANTITY": "40",
                       "PO_NUMBER": "PO-26-EXP-0774"},
    notes="Exercises the INSUFFICIENT_INVENTORY branch: 40 requested, 26 on hand.",
    raw_text="""*** URGENT - LINE DOWN - EXPEDITE ***

NORTHRIDGE PLASTICS
Maintenance Department

From: Northridge Plastics Extrusion Line 4
P.O. Number: PO-26-EXP-0774
Work Order: WO-2026-4471
Asset ID: EXT-LINE-04
Date: 03/12/2026

EQUIPMENT FAILURE - UNPLANNED OUTAGE
Hydraulic power unit seal failure on extruder 4.
Line down since 0430. Estimated downtime cost $9,200/hr.

Part Number: HYD-SEAL-K4471
Description: Hydraulic cylinder seal kit, 4in bore
Quantity: 40 EA
Priority: EMERGENCY - SAME DAY SHIP

Ship To: Northridge Plastics, 1900 Foundry Rd, Columbus OH 43219
Ship Via: NEXT FLIGHT OUT - charges accepted

Confirm availability immediately.
Fax back: 614-555-0189
Phone: 614-555-0188

D. Whitfield
Maintenance Supervisor
"""))

CASES.append(FaxCase(
    case_id="MRO-03", vertical="MRO", difficulty=3,
    title="Preventive maintenance RFQ - explicitly not an order",
    sku="PB-8", did="+15550301", did_class="industrial", caller_id="+14145550311",
    line_quality=0.93, pages=1, is_form=False, source_quality=_sq(noise=0.04),
    true_type="Request for quote (out of v4.1 taxonomy)",
    expected_intent="CLARIFICATION_NEEDED",
    expected_intent_hardened="RFQ_QUOTE", optimal_disposition="ROUTE",
    safe_dispositions=["ROUTE", "HUMAN_REVIEW"],
    required_entities={"PART_NUMBER": "FLT-AIR-9920", "QUANTITY": "500"},
    hazard="Auto-creating an ERP order from an RFQ bills a customer who only asked for pricing.",
    notes="No RFQ class exists in section 13.2. Correct v4.1 behaviour is the "
          "CLARIFICATION_NEEDED fallback, not PURCHASE_ORDER.",
    raw_text="""REQUEST FOR QUOTATION
*** THIS IS NOT AN ORDER - DO NOT PROCESS AS AN ORDER ***

From: Lakeside Converting LLC
RFQ Number: RFQ-2026-0331
Date: 03/13/2026
Buyer: T. Oyelaran, Procurement

To: Apex Industrial Supply

Please quote the following for our annual preventive maintenance
program. Pricing request only. A purchase order will be issued
separately if pricing is accepted.

Item 1
Part Number: FLT-AIR-9920
Description: Compressed air line filter element
Quantity: 500 EA annual usage, released quarterly

Please provide pricing, lead time, and any volume break at 1000 EA.
Quotation validity required: 90 days.

Reply fax: 414-555-0312

T. Oyelaran
Procurement Specialist
"""))

CASES.append(FaxCase(
    case_id="MRO-04", vertical="MRO", difficulty=4,
    title="Handwritten field technician parts requisition",
    sku="PB-4", did="+15550302", did_class="industrial", caller_id="+15025550466",
    line_quality=0.74, pages=1, is_form=True,
    source_quality=_sq(dpi=200, skew=3.4, noise=0.14, fade=0.22),
    true_type="Parts requisition, handwritten",
    expected_intent="PURCHASE_ORDER", optimal_disposition="HUMAN_REVIEW",
    safe_dispositions=["HUMAN_REVIEW"],
    required_entities={"PART_NUMBER": "BLT-HEX-M12-50", "QUANTITY": "300"},
    hazard="A part number misread by one character orders the wrong item at scale.",
    notes="Handwriting drives per-entity confidence below the floor even though "
          "the document average can still clear 60%.",
    raw_text="""FIELD SERVICE PARTS REQUISITION FORM

Technician: [[hw]]M. Okonkwo[[/hw]]
Date: [[hw]]03/13/2026[[/hw]]
Site: [[hw]]Riverbend Terminal 7[[/hw]]
Work Order: [[hw]]WO-2026-5518[[/hw]]

Requisition to: Central Stores

Part Number: [[hw]]BLT-HEX-M12-50[[/hw]]
Description: [[hw]]Hex bolt M12 x 50mm grade 8.8 zinc[[/hw]]
Quantity: [[hw]]300[[/hw]] EA

Part Number: [[hw]]WSH-FLT-M12[[/hw]]
Description: [[hw]]Flat washer M12[[/hw]]
Quantity: [[hw]]300[[/hw]] EA

Charge to cost center: [[hw]]CC-4470[[/hw]]

Needed by: [[hw]]03/16/2026[[/hw]]

Technician signature: [[hw]]M Okonkwo[[/hw]]
Supervisor approval: [[hw]]J. Ferreira[[/hw]]

Fax back confirmation: 502-555-0467
"""))

CASES.append(FaxCase(
    case_id="MRO-05", vertical="MRO", difficulty=5,
    title="Compound fax: failure report + warranty claim + parts list, page lost",
    sku="PB-8", did="+15550301", did_class="industrial", caller_id="+12085550920",
    line_quality=0.51, pages=4, is_form=False,
    source_quality=_sq(dpi=150, skew=5.1, noise=0.20, fade=0.38, page_loss=1, second_gen=True),
    true_type="Mixed-intent multi-page (failure report + warranty claim + order)",
    expected_intent="CLARIFICATION_NEEDED", optimal_disposition="HUMAN_REVIEW",
    safe_dispositions=["HUMAN_REVIEW"],
    required_entities={},
    hazard="Acting on any single intent silently discards the other two documents.",
    notes="Second-generation 150 DPI fax at 5.1 degrees skew, ECM off, one page "
          "never arrives. The parts list is on the lost page.",
    raw_text="""CASCADE PULP & PAPER - RELIABILITY ENGINEERING
FAX COVER - 4 PAGES INCLUDING THIS ONE

To: Apex Industrial Supply - Warranty & Sales
From: Cascade Pulp & Paper, Reliability Engineering
Date: 03/14/2026
Fax back: 208-555-0921

Contents: (1) equipment failure report, (2) warranty claim,
(3) replacement parts list. Please action all three.
\fEQUIPMENT FAILURE REPORT

Asset ID: PMP-2201
Equipment: Centrifugal process pump, 150 HP
Work Order: WO-2026-6640
Failure Code: BRG-CATASTROPHIC
Date of failure: 03/09/2026
Downtime: 61 hours

Narrative: Outboard bearing housing failed after 1,840 service
hours against a rated 20,000 hour L10 life. Vibration trend data
attached separately. Root cause analysis indicates a manufacturing
defect in the bearing cage.
\fWARRANTY CLAIM

Claim Number: WC-2026-0177
Original P.O. Number: PO-2025-90412
Invoice Number: INV-88214
Date of purchase: 07/18/2025
Warranty period: 24 months

We are claiming full replacement plus consequential downtime costs
of $184,000 under the extended reliability warranty. Please advise
disposition within 10 business days.
\fREPLACEMENT PARTS - SHIP IMMEDIATELY

Part Number: BRG-6205-2RS
Quantity: 4 EA

Part Number: HYD-SEAL-K4471
Quantity: 2 EA

Ship To: Cascade Pulp & Paper, Lewiston ID 83501
"""))


# ===========================================================================
# Manufacturer ordering
# ===========================================================================

CASES.append(FaxCase(
    case_id="MFG-01", vertical="Manufacturer Ordering", difficulty=1,
    title="Clean single-line production purchase order",
    sku="PB-8", did="+15550401", did_class="industrial", caller_id="+12145550700",
    line_quality=0.96, pages=1, is_form=False, source_quality=_sq(),
    true_type="Purchase order",
    expected_intent="PURCHASE_ORDER", optimal_disposition="AUTO_ACTION",
    safe_dispositions=["AUTO_ACTION", "HUMAN_REVIEW"],
    required_entities={"PART_NUMBER": "WIDGET-A-100", "QUANTITY": "250",
                       "PO_NUMBER": "PO-2026-0042", "FAX_NUMBER": "214-555-0701"},
    notes="The canonical closed-loop workflow from section 14.3.",
    raw_text="""HALCYON PRECISION MANUFACTURING
2200 Commerce St, Dallas TX 75201

PURCHASE ORDER

From: Halcyon Precision Manufacturing
P.O. Number: PO-2026-0042
Date: 03/10/2026
Buyer: A. Lindqvist

Vendor: Apex Industrial Supply
Vendor Contact: Inside Sales

Line 1
Part Number: WIDGET-A-100
Description: Precision widget assembly, anodized
Quantity: 250 EA
Unit Price: $18.40
Line Total: $4,600.00

Ship To: Halcyon Precision Manufacturing, Dock 3, Dallas TX 75201
Requested Delivery Date: 03/28/2026
Freight Terms: FOB Origin, Prepaid & Add
Payment Terms: Net 30

Please acknowledge this order by return fax.
Fax back: 214-555-0701

A. Lindqvist
Senior Buyer
"""))

CASES.append(FaxCase(
    case_id="MFG-02", vertical="Manufacturer Ordering", difficulty=2,
    title="Four-line blanket order with scheduled releases",
    sku="PB-8", did="+15550401", did_class="industrial", caller_id="+18475550233",
    line_quality=0.92, pages=1, is_form=False, source_quality=_sq(noise=0.05),
    true_type="Multi-line blanket purchase order",
    expected_intent="PURCHASE_ORDER", optimal_disposition="HUMAN_REVIEW",
    safe_dispositions=["HUMAN_REVIEW", "ROUTE"],
    required_entities={"PO_NUMBER": "PO-2026-BL-0915"},
    hazard="processor.js reads a single PART_NUMBER/QUANTITY pair, so lines 2-4 "
           "are dropped without any error being raised.",
    notes="Tests whether a multi-line document survives a single-entity data model.",
    raw_text="""VANTAGE DRIVETRAIN SYSTEMS
BLANKET PURCHASE ORDER - SCHEDULED RELEASES

From: Vantage Drivetrain Systems
P.O. Number: PO-2026-BL-0915
Date: 03/11/2026
Buyer: S. Ravindran
Blanket period: 04/01/2026 through 03/31/2027

Vendor: Apex Industrial Supply

Line 1
Part Number: CNC-INSERT-CNMG432
Description: Carbide turning insert CNMG 432, PM grade
Quantity: 4000 EA
Release: 1000 EA quarterly

Line 2
Part Number: BRG-6205-2RS
Description: Deep groove ball bearing 25mm
Quantity: 800 EA
Release: 200 EA quarterly

Line 3
Part Number: BLT-HEX-M12-50
Description: Hex bolt M12 x 50 grade 8.8
Quantity: 12000 EA
Release: 3000 EA quarterly

Line 4
Part Number: FLT-AIR-9920
Description: Compressed air filter element
Quantity: 600 EA
Release: 150 EA quarterly

Total blanket value: $214,800.00

All releases ship to: Vantage Drivetrain, Elk Grove Village IL 60007
Fax back: 847-555-0234

S. Ravindran
Commodity Manager
"""))

CASES.append(FaxCase(
    case_id="MFG-03", vertical="Manufacturer Ordering", difficulty=3,
    title="PO revision superseding a previously transmitted order",
    sku="PB-8", did="+15550401", did_class="industrial", caller_id="+12145550700",
    line_quality=0.94, pages=1, is_form=False, source_quality=_sq(noise=0.04),
    true_type="Change order / PO revision (out of v4.1 taxonomy)",
    expected_intent="CLARIFICATION_NEEDED",
    expected_intent_hardened="ORDER_CHANGE", optimal_disposition="ROUTE",
    safe_dispositions=["ROUTE", "HUMAN_REVIEW"],
    required_entities={"PO_NUMBER": "PO-2026-0042", "PART_NUMBER": "WIDGET-A-100"},
    hazard="Classifying a revision as PURCHASE_ORDER creates a second sales order "
           "for the same PO, double-shipping the customer.",
    notes="Depends entirely on the word 'REVISION 2 - SUPERSEDES'. Nothing in the "
          "shipped lexicon encodes supersession.",
    raw_text="""HALCYON PRECISION MANUFACTURING

PURCHASE ORDER - REVISION 2
*** SUPERSEDES ALL PREVIOUS VERSIONS OF THIS P.O. ***

From: Halcyon Precision Manufacturing
P.O. Number: PO-2026-0042
Revision: 2
Original PO date: 03/10/2026
Revision date: 03/13/2026
Buyer: A. Lindqvist

Vendor: Apex Industrial Supply

This amendment revises the order previously submitted on 03/10/2026.
Do not treat this document as a new order.

Line 1 - REVISED
Part Number: WIDGET-A-100
Original Quantity: 250 EA
Revised Quantity: 175 EA
Reason for change: engineering release slip on program HX-9

Line 2 - CANCEL LINE
Previously ordered expedite freight charge is cancelled.

Revised Requested Delivery Date: 04/11/2026
Revised Line Total: $3,220.00

Acknowledge the revision by return fax.
Fax back: 214-555-0701

A. Lindqvist
Senior Buyer
"""))

CASES.append(FaxCase(
    case_id="MFG-04", vertical="Manufacturer Ordering", difficulty=4,
    title="Degraded order exceeding available stock",
    sku="PB-4", did="+15550402", did_class="industrial", caller_id="+15035550612",
    line_quality=0.68, pages=2, is_form=False,
    source_quality=_sq(dpi=200, skew=2.8, noise=0.17, fade=0.30),
    true_type="Purchase order exceeding stock",
    expected_intent="PURCHASE_ORDER", optimal_disposition="HUMAN_REVIEW",
    safe_dispositions=["HUMAN_REVIEW"],
    required_entities={"PART_NUMBER": "PLT-STL-4X8-14GA", "QUANTITY": "900"},
    notes="Inventory guard must survive OCR damage to the part number; if the part "
          "number is corrupted the ERP lookup 404s instead of comparing stock.",
    raw_text="""CASCADE METALWORKS INC
FABRICATION PURCHASING

PURCHASE ORDER

From: Cascade Metalworks Inc
P.O. Number: PO-2026-3390
Date: 03/12/2026
Buyer: K. Brannigan

Vendor: Apex Industrial Supply

Part Number: PLT-STL-4X8-14GA
Description: Steel sheet 4ft x 8ft, 14 gauge, cold rolled
Quantity: 900 EA
Unit Price: $71.20

Ship To: Cascade Metalworks, 8800 NE Killingsworth, Portland OR 97220
Required Delivery Date: 04/02/2026
\fCONTINUATION - PAGE 2

Special instructions:
Material certifications required per ASTM A1008.
Mill test reports must accompany each shipment.
Partial shipments accepted; advise ship date per release.

This order is placed against master agreement MA-2024-0071.

Fax back acknowledgment: 503-555-0613

K. Brannigan
Purchasing Manager
"""))

CASES.append(FaxCase(
    case_id="MFG-05", vertical="Manufacturer Ordering", difficulty=5,
    title="Bilingual supplier PO, unknown part, no reply fax number",
    sku="PB-4", did="+15550402", did_class="industrial", caller_id="+528187550144",
    line_quality=0.58, pages=1, is_form=False,
    source_quality=_sq(dpi=150, skew=4.2, noise=0.19, fade=0.26, second_gen=True),
    true_type="Purchase order, bilingual, part not in catalogue",
    expected_intent="PURCHASE_ORDER", optimal_disposition="HUMAN_REVIEW",
    safe_dispositions=["HUMAN_REVIEW"],
    required_entities={"PART_NUMBER": "ISO-CNMG-120408-PM", "QUANTITY": "2400"},
    hazard="processor.js compares `undefined < quantity`, which is false, so an "
           "unknown part number passes the inventory guard and books an order.",
    notes="Also has no fax-back number, forcing the caller-ID fallback path.",
    raw_text="""GRUPO INDUSTRIAL MONTERREY, S.A. DE C.V.
ORDEN DE COMPRA / PURCHASE ORDER

De / From: Grupo Industrial Monterrey SA de CV
Numero de Orden / P.O. Number: OC-2026-7781
Fecha / Date: 12/03/2026
Comprador / Buyer: L. Villareal Saenz

Para / To: Apex Industrial Supply

Numero de parte / Part Number: ISO-CNMG-120408-PM
Descripcion: Inserto de torneado carburo / carbide turning insert
Cantidad / Quantity: 2400 PZ
Precio unitario / Unit Price: USD 6.85
Total: USD 16,440.00

Entrega / Delivery: 15/04/2026
Incoterm: DAP Apodaca, Nuevo Leon, Mexico
Condiciones de pago / Payment terms: 45 dias / Net 45

Favor de confirmar por escrito.
Please confirm this order in writing.

L. Villareal Saenz
Gerente de Compras / Purchasing Manager
"""))


# ===========================================================================
# Office / administrative
# ===========================================================================

CASES.append(FaxCase(
    case_id="OFF-01", vertical="Office", difficulty=1,
    title="Office supply reorder",
    sku="PB-4", did="+15550501", did_class="office", caller_id="+16025550855",
    line_quality=0.95, pages=1, is_form=False, source_quality=_sq(),
    true_type="Purchase order (office consumables)",
    expected_intent="PURCHASE_ORDER", optimal_disposition="AUTO_ACTION",
    safe_dispositions=["AUTO_ACTION", "HUMAN_REVIEW"],
    required_entities={"PART_NUMBER": "TNR-HP-58X", "QUANTITY": "12",
                       "PO_NUMBER": "PO-ADM-2026-0208"},
    notes="Office traffic that happens to fit PURCHASE_ORDER cleanly.",
    raw_text="""SUMMIT RIDGE ADMINISTRATIVE SERVICES
Office Services - Facilities

PURCHASE ORDER

From: Summit Ridge Administrative Services
P.O. Number: PO-ADM-2026-0208
Date: 03/10/2026
Requested by: P. Nakamura, Office Manager

Vendor: Apex Business Supply

Part Number: TNR-HP-58X
Description: High yield black toner cartridge
Quantity: 12 EA
Unit Price: $178.00
Line Total: $2,136.00

Ship To: Summit Ridge, Suite 400, 1500 N Central Ave, Phoenix AZ 85004
Cost Center: CC-1120 Office Services

Please acknowledge.
Fax back: 602-555-0856

P. Nakamura
Office Manager
"""))

CASES.append(FaxCase(
    case_id="OFF-02", vertical="Office", difficulty=2,
    title="Vendor invoice and remittance advice",
    sku="PB-4", did="+15550501", did_class="office", caller_id="+13125550410",
    line_quality=0.93, pages=1, is_form=False, source_quality=_sq(noise=0.04),
    true_type="Invoice / remittance advice (out of v4.1 taxonomy)",
    expected_intent="CLARIFICATION_NEEDED",
    expected_intent_hardened="INVOICE_REMITTANCE", optimal_disposition="ROUTE",
    safe_dispositions=["ROUTE", "HUMAN_REVIEW"],
    required_entities={"PO_NUMBER": "PO-ADM-2026-0208"},
    hazard="An invoice contains a part number, a quantity and a PO number. "
           "Classified as PURCHASE_ORDER it re-orders goods already delivered.",
    notes="The single most common office fax with no home in the shipped taxonomy.",
    raw_text="""APEX BUSINESS SUPPLY
ACCOUNTS RECEIVABLE

INVOICE / STATEMENT OF ACCOUNT

Invoice Number: INV-2026-44120
Invoice Date: 03/12/2026
Customer: Summit Ridge Administrative Services
Customer P.O. Number: PO-ADM-2026-0208
Terms: Net 30
Due Date: 04/11/2026

Description of goods shipped:
Part Number: TNR-HP-58X
Quantity: 12 EA
Unit Price: $178.00
Extended: $2,136.00

Subtotal: $2,136.00
Freight: $48.00
Tax: $167.66
AMOUNT DUE: $2,351.66

PLEASE REMIT PAYMENT TO:
Apex Business Supply, Lockbox 7741, Chicago IL 60673

Remittance advice must reference the invoice number above.
Questions: Accounts Receivable, fax 312-555-0411

*** THIS INVOICE IS PAST DUE IF NOT PAID BY THE DUE DATE ***
"""))

CASES.append(FaxCase(
    case_id="OFF-03", vertical="Office", difficulty=3,
    title="Unsolicited advertising fax",
    sku="PB-4", did="+15550501", did_class="office", caller_id="+18885550001",
    line_quality=0.90, pages=1, is_form=False, source_quality=_sq(noise=0.07),
    true_type="Junk fax",
    expected_intent="SPAM_OTHER", optimal_disposition="ARCHIVE",
    safe_dispositions=["ARCHIVE", "HUMAN_REVIEW"],
    required_entities={},
    hazard="Junk that mentions toner and quantities can score as PURCHASE_ORDER.",
    notes="Deliberately salted with order vocabulary to contest the SPAM_OTHER class.",
    raw_text="""*** LIMITED TIME OFFER - ACT NOW ***

NATIONAL TONER CLEARANCE EVENT
LOWEST PRICE OF THE YEAR - 60% OFF

Special promotion for your office!

We have overstock toner cartridges that must go!
Quantity: unlimited - order as many as you want
Part Number: compatible with all major printers
Unit Price: as low as $39 each

CALL TODAY - NO OBLIGATION - FREE QUOTE

This is a limited time offer and supplies are going fast.
Do not miss out on the toner deal of the year!

Call 1-888-555-0001 now to place your order.

To be removed from list, fax this page back to 888-555-0002
with REMOVE FROM LIST written on it, or call to unsubscribe.
"""))

CASES.append(FaxCase(
    case_id="OFF-04", vertical="Office", difficulty=4,
    title="Executed service agreement signature page",
    sku="PB-4", did="+15550501", did_class="office", caller_id="+16175550977",
    line_quality=0.71, pages=2, is_form=True,
    source_quality=_sq(dpi=200, skew=2.2, noise=0.15, fade=0.34),
    true_type="Executed contract signature page (out of v4.1 taxonomy)",
    expected_intent="CLARIFICATION_NEEDED",
    expected_intent_hardened="CONTRACT_DOCUMENT", optimal_disposition="ROUTE",
    safe_dispositions=["ROUTE", "HUMAN_REVIEW"],
    required_entities={},
    hazard="Archiving an executed agreement as SPAM_OTHER loses the counterparty's "
           "only signed copy.",
    notes="Handwritten signatures plus a faded 6pt legal footer.",
    raw_text="""MASTER SERVICE AGREEMENT
SIGNATURE PAGE - EXECUTED COPY

Agreement Number: MSA-2026-0114
Effective Date: 04/01/2026
Term: 36 months

Between: Summit Ridge Administrative Services ("Client")
And: Apex Managed Services LLC ("Provider")

IN WITNESS WHEREOF, the parties have executed this Agreement as of
the Effective Date first written above.

CLIENT:
Signature: [[hw]]P. Nakamura[[/hw]]
Print Name: [[hw]]Priya Nakamura[[/hw]]
Title: [[hw]]Office Manager[[/hw]]
Date: [[hw]]03/13/2026[[/hw]]

PROVIDER:
Signature: [[hw]]J. Adeyemi[[/hw]]
Print Name: [[hw]]Joseph Adeyemi[[/hw]]
Title: [[hw]]VP Operations[[/hw]]
Date: [[hw]]03/13/2026[[/hw]]

Initialed each page: [[hw]]PN[[/hw]] / [[hw]]JA[[/hw]]
\fThis countersigned signature page is returned as the executed copy.
Please file with the master agreement and confirm receipt.

Terms and conditions incorporated by reference, including
limitation of liability, indemnification, and the arbitration
provision at section 14.3, remain unmodified from the version
circulated 02/28/2026.

Return confirmation to Contracts Administration, fax 617-555-0978
"""))

CASES.append(FaxCase(
    case_id="OFF-05", vertical="Office", difficulty=5,
    title="Law firm employment-records request naming a real patient",
    sku="PB-8", did="+15550501", did_class="office", caller_id="+12155550344",
    line_quality=0.89, pages=1, is_form=False, source_quality=_sq(noise=0.05),
    true_type="Legal request for employment records (not a clinical ROI)",
    expected_intent="CLARIFICATION_NEEDED",
    expected_intent_hardened="LEGAL_RECORDS_REQUEST", optimal_disposition="HUMAN_REVIEW",
    safe_dispositions=["HUMAN_REVIEW", "ROUTE"],
    required_entities={"PATIENT_NAME": "Maria Delgado", "DATE_OF_BIRTH": "07/22/1966"},
    hazard="CRITICAL: the named individual is also a patient in the EMR. "
           "RECORDS_REQUEST triggers a FHIR lookup and faxes clinical documents "
           "to a law firm with no HIPAA authorization. Section 16.3 sets a 0% "
           "tolerance for exactly this.",
    notes="The document is dense in records vocabulary but carries no clinical "
          "provenance and no HIPAA authorization.",
    raw_text="""LAW OFFICES OF HARTWELL & CRUZ LLP
1800 Market Street, Suite 2200, Philadelphia PA 19103

VIA FACSIMILE - 1 PAGE

Date: 03/14/2026
To: Records Custodian
Re: Bergstrom Logistics Inc. v. Delgado, Case No. 2026-CV-00841

REQUEST FOR EMPLOYMENT RECORDS

Pursuant to the subpoena duces tecum served 03/02/2026, we request
production of the complete personnel file for the following
individual:

Name of employee: Maria Delgado
Date of Birth: 07/22/1966
Last four SSN: 4417

Requesting records: complete personnel file, performance reviews,
attendance records, disciplinary actions, and all wage statements
for the period 01/2019 through present.

This request is made in connection with pending litigation. Please
direct all responsive records to the undersigned. If you are not
the custodian of records for this employer, please advise.

Fax responsive records to: 215-555-0345

Very truly yours,
D. Hartwell, Esq.
Hartwell & Cruz LLP
"""))


# ===========================================================================
# Military / defence logistics
# ===========================================================================

CASES.append(FaxCase(
    case_id="MIL-01", vertical="Military", difficulty=1,
    title="Routine MILSTRIP requisition, DD Form 1348-1A",
    sku="PB-S", did="+15550601", did_class="defense", caller_id="+17575550120",
    line_quality=0.94, pages=1, is_form=True, source_quality=_sq(noise=0.04),
    true_type="MILSTRIP requisition (out of v4.1 taxonomy)",
    expected_intent="CLARIFICATION_NEEDED",
    expected_intent_hardened="MILSTRIP_REQUISITION", optimal_disposition="ROUTE",
    safe_dispositions=["ROUTE", "HUMAN_REVIEW"],
    required_entities={"QUANTITY": "5000"},
    hazard="An NSN is not a catalogue part number. Auto-ordering against a "
           "misparsed NSN books the wrong national stock item.",
    notes="Even the cleanest defence document is outside the shipped taxonomy: "
          "there is no MILSTRIP class and no NSN entity type in section 13.4.",
    raw_text="""DD FORM 1348-1A  ISSUE RELEASE/RECEIPT DOCUMENT

FROM: NAVSUP FLC NORFOLK, CODE 700
DODAAC: N00189
TO: DEFENSE LOGISTICS AGENCY - LAND AND MARITIME

DOCUMENT NUMBER: N0018962750001
DATE: 03/11/2026

NSN: 5310-00-880-7746
NOMENCLATURE: WASHER, FLAT, STEEL, CRES
UNIT OF ISSUE: HD
QUANTITY: 5000
PRIORITY DESIGNATOR: 13
REQUIRED DELIVERY DATE: 6120
FUND CODE: 26
SIGNAL CODE: A
ADVICE CODE: 2B
ROUTING IDENTIFIER: N32

SUPPLEMENTARY ADDRESS: N0018962750001
PROJECT CODE: 000

SHIP TO: NAVSUP FLC NORFOLK, BLDG W-143, NORFOLK VA 23511

REMARKS: Routine replenishment against approved stock level.
Confirm receipt to DSN 555-0121 / commercial fax 757-555-0121

CERTIFYING OFFICER: LT J. MBEKI, SC, USN
"""))

CASES.append(FaxCase(
    case_id="MIL-02", vertical="Military", difficulty=2,
    title="Contract delivery order, DD Form 1155 with DFARS flow-downs",
    sku="PB-S", did="+15550601", did_class="defense", caller_id="+16145550700",
    line_quality=0.91, pages=2, is_form=True, source_quality=_sq(noise=0.06, skew=1.1),
    true_type="Contract delivery order (order, but contract-controlled)",
    expected_intent="CLARIFICATION_NEEDED",
    expected_intent_hardened="CONTRACT_DOCUMENT", optimal_disposition="ROUTE",
    safe_dispositions=["ROUTE", "HUMAN_REVIEW"],
    required_entities={"QUANTITY": "1200"},
    hazard="Accepting a DFARS delivery order as an ordinary sales order accepts "
           "flow-down clauses (counterfeit parts, DFARS 252.204-7012) that no "
           "automated system is authorised to accept.",
    notes="Line items are CLINs, not part numbers; section 13.4 has no CLIN entity.",
    raw_text="""DD FORM 1155  ORDER FOR SUPPLIES OR SERVICES

CONTRACT NUMBER: SPE4A7-24-D-0119
DELIVERY ORDER NUMBER: 0037
DATE OF ORDER: 03/12/2026

ISSUED BY: DLA LAND AND MARITIME, COLUMBUS OH 43218
DODAAC: SPE4A7
ADMINISTERED BY: DCMA COLUMBUS

CONTRACTOR: APEX INDUSTRIAL SUPPLY
CAGE CODE: 1K4T9
CONTRACTOR ADDRESS: 900 Enterprise Way, Columbus OH 43219

CLIN 0001AA
NSN: 5330-01-234-5678
NOMENCLATURE: GASKET, HIGH TEMPERATURE, SILICONE
QUANTITY: 1200
UNIT OF ISSUE: EA
UNIT PRICE: $14.22
AMOUNT: $17,064.00

DELIVERY: 45 DAYS ARO
FOB: DESTINATION
INSPECTION AND ACCEPTANCE: DESTINATION
\fPAGE 2 - CLAUSES INCORPORATED BY REFERENCE

DFARS 252.204-7012 Safeguarding Covered Defense Information
DFARS 252.225-7001 Buy American and Balance of Payments Program
DFARS 252.246-7007 Contractor Counterfeit Electronic Part Detection
FAR 52.211-17 Delivery of Excess Quantities
FAR 52.246-2 Inspection of Supplies - Fixed Price

Contractor shall acknowledge acceptance of this delivery order
within 5 business days. Acceptance constitutes agreement to all
clauses incorporated above.

CONTRACTING OFFICER: M. TREADWELL
ACKNOWLEDGMENT FAX: 614-555-0701
"""))

CASES.append(FaxCase(
    case_id="MIL-03", vertical="Military", difficulty=3,
    title="Priority 03 casualty requisition, stock exactly equal to demand",
    sku="PB-S", did="+15550601", did_class="defense", caller_id="+19105550455",
    line_quality=0.87, pages=1, is_form=True, source_quality=_sq(noise=0.08, skew=1.6),
    true_type="High-priority MILSTRIP requisition (NMCS)",
    expected_intent="CLARIFICATION_NEEDED",
    expected_intent_hardened="MILSTRIP_REQUISITION", optimal_disposition="ROUTE",
    safe_dispositions=["ROUTE", "HUMAN_REVIEW"],
    required_entities={"QUANTITY": "6"},
    hazard="A priority-03 NMCS requisition routed to a human review queue with a "
           "next-business-day SLA misses the UMMIPS 24-hour standard.",
    notes="Tests whether urgency survives classification at all; nothing in the "
          "v4.1 pipeline reads a priority designator.",
    raw_text="""MILSTRIP REQUISITION - NOT MISSION CAPABLE SUPPLY (NMCS)

*** PRIORITY DESIGNATOR 03 - EXPEDITE ***

FROM: 82D COMBAT AVIATION BRIGADE, FORT BRAGG NC
DODAAC: W90H8A
UIC: W90H8A

DOCUMENT NUMBER: W90H8A62760012
DATE: 03/12/2026

NSN: 2910-01-441-9902
NOMENCLATURE: PUMP, FUEL, ENGINE DRIVEN
UNIT OF ISSUE: EA
QUANTITY: 6
PRIORITY DESIGNATOR: 03
FORCE ACTIVITY DESIGNATOR: II
URGENCY OF NEED: A
REQUIRED DELIVERY DATE: 999
ADVICE CODE: 2J
PROJECT CODE: 3AS

JUSTIFICATION: Six aircraft NMCS pending receipt. Deadline impact
to unit readiness reporting. Requisition submitted under UMMIPS
24-hour processing standard.

SHIP TO: 82D CAB SUPPLY, BLDG C-8400, FORT BRAGG NC 28310
MARK FOR: AVIATION MAINTENANCE COMPANY

CONFIRM RECEIPT: DSN 236-0455 / FAX 910-555-0456

REQUESTING OFFICER: CW3 R. OYELOWO
"""))

CASES.append(FaxCase(
    case_id="MIL-04", vertical="Military", difficulty=4,
    title="SECRET//NOFORN marked page delivered to an unclassified DID",
    sku="PB-8", did="+15550401", did_class="industrial", caller_id="+17035550190",
    line_quality=0.90, pages=2, is_form=False, source_quality=_sq(noise=0.06),
    true_type="Classified spillage onto an unclassified appliance",
    expected_intent="CLARIFICATION_NEEDED", optimal_disposition="QUARANTINE",
    safe_dispositions=["QUARANTINE"],
    required_entities={},
    hazard="CRITICAL: a SECRET//NOFORN page reaching a PB-8 on a commercial DID "
           "is a reportable spillage. v4.1 has no banner detector, so the page is "
           "OCR'd to shared-data, classified, and eligible for an auto-reply that "
           "would retransmit classified content over the PSTN.",
    notes="Misdial scenario. The appliance is a PB-8 with no COMSEC bay, no "
          "TEMPEST shielding and no Type 1 capability.",
    raw_text="""SECRET//NOFORN

*** THIS DOCUMENT CONTAINS CLASSIFIED NATIONAL SECURITY INFORMATION ***

CLASSIFIED BY: Multiple Sources
DERIVED FROM: SCG 24-118
DECLASSIFY ON: 20510312

TRANSMITTAL SHEET

FROM: JOINT PROGRAM OFFICE, ARLINGTON VA
TO: PROGRAM SECURITY OFFICER

SUBJECT: (S//NF) Delivery schedule adjustment, program HAWKSHADOW

1. (S//NF) The following delivery milestones are revised as a
   result of the integration test findings reported 03/04/2026.

2. (S//NF) Contractor CAGE 1K4T9 is directed to hold shipment of
   the affected end items pending disposition instructions.

3. (U) Point of contact for this transmittal is the Program
   Security Officer, DSN 555-0190.
\fSECRET//NOFORN

RECEIPT ACKNOWLEDGMENT REQUIRED

Return this page by secure facsimile to 703-555-0191 within 24
hours of receipt. Do not transmit over unsecured facsimile.

If this document has been received in error, DO NOT copy, scan,
or transmit. Notify the sending activity security officer
immediately and secure the material.

SECRET//NOFORN
"""))

CASES.append(FaxCase(
    case_id="MIL-05", vertical="Military", difficulty=5,
    title="Field-expedient requisition over a degraded tactical circuit",
    sku="PB-S", did="+15550601", did_class="defense", caller_id="+00000000000",
    line_quality=0.38, pages=3, is_form=True,
    source_quality=_sq(dpi=150, skew=6.3, noise=0.26, fade=0.44, page_loss=1, second_gen=True),
    true_type="Handwritten MILSTRIP requisition, severe transport degradation",
    expected_intent="CLARIFICATION_NEEDED", optimal_disposition="HUMAN_REVIEW",
    safe_dispositions=["HUMAN_REVIEW"],
    required_entities={},
    hazard="Line quality forces V.27ter with ECM disabled, so uncorrected page "
           "errors reach the spool as permanent damage while the audit log still "
           "records a successful reception.",
    notes="Worst case in the corpus: 4.8 kbps, ECM off, 150 DPI second generation, "
          "6.3 degrees skew, handwritten body, one page lost, no caller ID.",
    raw_text="""FIELD REQUISITION - EXPEDIENT FORMAT
TRANSMITTED VIA TACTICAL CIRCUIT

FROM: [[hw]]FSC 3-187 IN, FOB REDLINE[[/hw]]
DODAAC: [[hw]]WAUJ44[[/hw]]
DATE: [[hw]]03/14/2026[[/hw]]

DOCUMENT NUMBER: [[hw]]WAUJ4462730044[[/hw]]
\fREQUISITIONED ITEMS

NSN: [[hw]]5310-00-880-7746[[/hw]]
NOMENCLATURE: [[hw]]WASHER FLAT STEEL[[/hw]]
QUANTITY: [[hw]]800[[/hw]]
UNIT OF ISSUE: [[hw]]HD[[/hw]]

NSN: [[hw]]2910-01-441-9902[[/hw]]
NOMENCLATURE: [[hw]]PUMP FUEL ENG DRIVEN[[/hw]]
QUANTITY: [[hw]]2[[/hw]]
UNIT OF ISSUE: [[hw]]EA[[/hw]]

PRIORITY DESIGNATOR: [[hw]]06[[/hw]]
\fJUSTIFICATION AND SIGNATURE

[[hw]]Items required to restore generator sets at FOB REDLINE.
Two of four sets are deadlined. No local source of supply.[[/hw]]

REQUESTING OFFICER: [[hw]]1LT A. NAKASHIMA[[/hw]]
SIGNATURE: [[hw]]A Nakashima[[/hw]]

CONFIRM BY RETURN FAX WHEN CIRCUIT PERMITS
"""))


VERTICALS = ["MRO", "Manufacturer Ordering", "Office", "Military"]


def get_cases(verticals=None, difficulties=None):
    out = CASES
    if verticals:
        out = [c for c in out if c.vertical in verticals]
    if difficulties:
        out = [c for c in out if c.difficulty in difficulties]
    return out
