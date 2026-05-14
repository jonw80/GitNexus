# UGCT Y4 Chow-ring supported tensor export
# Runs under SageMath, but intentionally uses plain Python data structures so the
# exact arithmetic is transparent and reproducible.
#
# This computes the certificate-grade supported sector from the currently
# supplied global data:
#   - dP8 surface intersection form
#   - B3 = P(O + K_dP8) projective-bundle relation R(R-K)=0
#   - smooth elliptic zero-section relation Z^2 = -c1(B3) Z
#   - generic SU(5) A4 Cartan-pair pushforward over S=dP8
# It DOES NOT claim chamber-specific exceptional self-intersections with >=3
# Cartan/exceptional factors; those require the full resolved ambient SR and
# linear-equivalence ideals.

import json, itertools, os, hashlib
from fractions import Fraction

base_basis = ["R", "H"] + [f"E{i}" for i in range(1, 9)]
basis = base_basis + ["Z"] + [f"C{i}" for i in range(1, 5)]

# canonical class K_dP8 = -3H + sum_i E_i represented in surface basis H,E1..E8
K = {"H": Fraction(-3)}
for i in range(1, 9):
    K[f"E{i}"] = Fraction(1)

# c1(B3) for B3=P(O+K_S) over S=dP8 using quotient convention:
# c1(B3)=2R-2K_S.
c1B = {"R": Fraction(2), "H": Fraction(6)}
for i in range(1, 9):
    c1B[f"E{i}"] = Fraction(-2)

def surf_pair(a, b):
    if a == "H" and b == "H":
        return Fraction(1)
    if a.startswith("E") and b.startswith("E") and a == b:
        return Fraction(-1)
    return Fraction(0)

def pair_vec(v, w):
    s = Fraction(0)
    for a, ca in v.items():
        for b, cb in w.items():
            s += ca * cb * surf_pair(a, b)
    return s

def class_vec(name):
    if name == "R":
        return {"R": Fraction(1)}
    if name == "H":
        return {"H": Fraction(1)}
    if name.startswith("E") and name[1:].isdigit():
        return {name: Fraction(1)}
    raise ValueError(name)

def surf_vec(name):
    if name == "H": return {"H": Fraction(1)}
    if name.startswith("E") and name[1:].isdigit(): return {name: Fraction(1)}
    raise ValueError(name)

def K_pair(name):
    return pair_vec(K, surf_vec(name))

def K_square():
    return pair_vec(K, K)

def b3_triple(a, b, c):
    names = [a, b, c]
    rcount = names.count("R")
    surf = [x for x in names if x != "R"]
    if rcount == 0:
        return Fraction(0)
    if rcount == 1:
        if len(surf) != 2: return Fraction(0)
        return surf_pair(surf[0], surf[1])
    if rcount == 2:
        if len(surf) != 1: return K_square()
        return K_pair(surf[0])
    if rcount == 3:
        return K_square()
    return Fraction(0)

def multiply_linear(poly, lin):
    # poly maps tuple of base divisors sorted by input order to coefficient.
    out = {}
    for mon, coeff in poly.items():
        for d, cd in lin.items():
            out[mon + (d,)] = out.get(mon + (d,), Fraction(0)) + coeff * cd
    return {k:v for k,v in out.items() if v}

def z_vertical_intersection(mon):
    # mon is a 4-tuple with no Cartans. Reduce Z^n via Z^2=-c1B Z.
    zc = mon.count("Z")
    base = [x for x in mon if x != "Z"]
    if zc == 0:
        return Fraction(0)
    # Z^zc = (-c1B)^(zc-1) Z
    poly = {tuple(base): Fraction(1)}
    minus_c1 = {k: -v for k,v in c1B.items()}
    for _ in range(zc - 1):
        poly = multiply_linear(poly, minus_c1)
    total = Fraction(0)
    for base_mon, coeff in poly.items():
        if len(base_mon) == 3:
            total += coeff * b3_triple(*base_mon)
    return total

A4 = [
    [2,-1,0,0],
    [-1,2,-1,0],
    [0,-1,2,-1],
    [0,0,-1,2],
]

def cartan_pair_intersection(mon):
    cart = [x for x in mon if x.startswith("C")]
    non = [x for x in mon if not x.startswith("C")]
    if len(cart) != 2 or "Z" in non or len(non) != 2:
        return None
    i = int(cart[0][1:]) - 1
    j = int(cart[1][1:]) - 1
    # C_i C_j D_a D_b = -A_ij * int_B S D_a D_b, S=R.
    return Fraction(-A4[i][j]) * b3_triple("R", non[0], non[1])

nonzero = {}
unsupported = []
zero = 0
for mon in itertools.combinations_with_replacement(basis, 4):
    cart_count = sum(1 for x in mon if x.startswith("C"))
    val = None
    if cart_count == 0:
        val = z_vertical_intersection(mon)
    elif cart_count == 2:
        val = cartan_pair_intersection(mon)
        if val is None:
            unsupported.append(",".join(mon)); continue
    else:
        unsupported.append(",".join(mon)); continue
    if val:
        nonzero[",".join(mon)] = str(val) if val.denominator != 1 else int(val)
    else:
        zero += 1

report = {
    "status": "SAGE_SUPPORTED_DEGREE4_TENSOR_EXPORTED__FULL_ESOLE_YAU_SELF_EXCEPTIONAL_BLOCK_UNSUPPORTED",
    "basis": basis,
    "basis_size": len(basis),
    "total_symmetric_multisets_degree4": len(list(itertools.combinations_with_replacement(basis,4))),
    "nonzero_exported": len(nonzero),
    "zero_multisets": zero,
    "unsupported_multisets": len(unsupported),
    "checks": {
        "K_dP8_square": str(K_square()),
        "K_dP8_square_equals_1": K_square() == 1,
        "A4_cartan_matrix_used": A4,
        "B3_projective_bundle_relation": "R^2=R*K_dP8",
        "zero_section_relation": "Z^2=-c1(B3)Z",
        "full_chamber_specific_tensor_verified": False
    },
    "quadruple_intersections_supported": nonzero,
    "unsupported_reason": "Requires complete resolved ambient SR ideal, linear-equivalence ideal, and chamber-specific exceptional pushforward data for monomials with >=3 Cartan/exceptional factors or Z-Cartan mixing.",
    "unsupported_multisets_sample": unsupported[:100]
}
os.makedirs("reports", exist_ok=True)
os.makedirs("data", exist_ok=True)
with open("data/y4_intersection_ring_supported_sage_export.json", "w") as f:
    json.dump(report, f, indent=2, sort_keys=True)
with open("reports/sage_run_summary.json", "w") as f:
    json.dump({k: report[k] for k in ["status","basis_size","total_symmetric_multisets_degree4","nonzero_exported","zero_multisets","unsupported_multisets","checks"]}, f, indent=2, sort_keys=True)
print(json.dumps({k: report[k] for k in ["status","nonzero_exported","unsupported_multisets","checks"]}, indent=2, sort_keys=True))
