#!/usr/bin/env python3
"""Rigorous lower bound for the genuine finite Wilson Perron eigenvalue.

Only exact rational variational parameters enter the certificate. An optional
earlier floating point pilot merely suggested their values. No optimization
claim or affine-log identification is needed by the proof.
"""
from collections import Counter
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "dag_closeout_v5"))
from certify_wilson import wilson_table
from intervals import I

BETA = F(271, 20)
TREE = [0, 1, 2, 3, 4, 6, 9]
# Assigned in increasing free-edge order; all numbers are exact rationals.
EDGE_NUMERATORS = [449681,438932,471181,438932,449188,426516,450555,
                   450314,426516,450555,428388,416594,427146,429912,
                   416594,427146,427895]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def exp_interval(x):
    """Positive Taylor sum, geometric remainder, then repeated squaring."""
    x = I(x)
    assert x.lo >= 0
    power = 0
    while x.hi > 1:
        x /= 2
        power += 1
    term = total = I(1)
    for n in range(1, 121):
        term = term*x/n
        total += term
    first = term*x/121
    tail = first/(1-x/122)
    result = total + I(0, tail.hi)
    for _ in range(power):
        result *= result
    return result


def is_tree(edges):
    parents = list(range(8))
    def root(v):
        while parents[v] != v:
            v = parents[v]
        return v
    for e in edges:
        u, mu = divmod(e, 3)
        u, v = root(u), root(u ^ (1 << (2-mu)))
        if u == v:
            return False
        parents[u] = v
    return len(edges) == 7


def geometry_and_profiles():
    raw = (ROOT / "full_moments_v4/geometry.bin").read_bytes()
    assert raw[:8] == b"YMGEOM04"
    links = np.frombuffer(raw, np.uint8, count=96, offset=520).reshape(24, 4)
    signs = np.frombuffer(raw, np.int8, count=96, offset=616).reshape(24, 4)
    assert all(len(set(map(int, row))) == 4 for row in links)
    assert is_tree(TREE)
    profiles = Counter()
    for tree in itertools.combinations(range(24), 7):
        if not is_tree(tree):
            continue
        chosen = set(tree)
        ks = [sum(int(e) not in chosen for e in row) for row in links]
        profiles[tuple(ks.count(k) for k in range(5))] += 1
    assert sum(profiles.values()) == 49152
    selected = set(TREE)
    ks = [sum(int(e) not in selected for e in row) for row in links]
    best = tuple(ks.count(k) for k in range(5))
    assert best == (0,4,6,4,10)
    dominance = []
    for counts, multiplicity in sorted(profiles.items()):
        d = [x-y for x,y in zip(best, counts)]
        # Difference = r(1-r)^2*(d1+d4*r), nonnegative for 0<=r<=1.
        assert d[0] == 0 and d[1] >= 0 and d[4] >= 0
        assert d[2] == d[4]-2*d[1] and d[3] == d[1]-2*d[4]
        dominance.append({"counts_by_remaining_edges_0_to4":counts,
                          "spanning_tree_count":multiplicity,
                          "difference_factor_coefficients":[d[1],d[4]]})
    return links, signs, best, dominance


def evaluate(links, parameters):
    free = [e for e in range(24) if e not in TREE]
    assert len(free) == 17 and len(parameters) == 17
    tables = {}
    for parameter in sorted(set(parameters)):
        t, z = wilson_table(parameter, [(0,0),(1,0)])
        r = t[16]["coefficient"]
        assert 0 < r.lo <= r.hi < 1
        tables[parameter] = r, z, z.log()
    r_by_edge = {e:tables[b][0] for e,b in zip(free, parameters)}
    spatial = I(0)
    plaquette_products = []
    for row in links:
        val = I(1)
        for e in row:
            if int(e) in r_by_edge:
                val *= r_by_edge[int(e)]
        spatial += val
        plaquette_products.append(val.record())
    spatial *= BETA
    entropy = sum((b*tables[b][0]-tables[b][2] for b in parameters), I(0))
    value = spatial-entropy
    return {
        "free_edge_indices":free,
        "rational_beta_prime_by_free_edge":[str(b) for b in parameters],
        "single_link_values":[{"exact_beta_prime":str(b),
                               "fundamental_normalized_coefficient":r.record(),
                               "one_link_partition_function":z.record(),
                               "log_partition_function":logz.record()}
                              for b,(r,z,logz) in sorted(tables.items())],
        "plaquette_mean_trace_divided_by3":plaquette_products,
        "mean_spatial_exponent":spatial.record(),
        "relative_entropy_to_Haar":entropy.record(),
        "variational_log_lower_bound":value.record(),
        "exponential_of_variational_bound":exp_interval(value).record(),
    }


def main():
    links, signs, best, dominance = geometry_and_profiles()
    isotropic = evaluate(links, [F(175,4)]*17)
    anisotropic = evaluate(links, [F(n,10000) for n in EDGE_NUMERATORS])
    assert I(anisotropic["variational_log_lower_bound"]["lower"]).lo > I(isotropic["variational_log_lower_bound"]["upper"]).hi
    lower = anisotropic["variational_log_lower_bound"]["lower"]
    result = {
        "schema":"YM_GENUINE_WILSON_PERRON_GAUGE_FIXED_LOWER_V11",
        "status":"PASS_RIGOROUS_LOWER_BOUND_ONLY",
        "operator":"T=M_s C_beta M_s, s=exp((beta/6) sum_24 ReTr U_p), C_beta1=1",
        "exact_beta":str(BETA),
        "physical_space":"Full gauge-invariant finite-volume SU(3)^24 Hilbert space, all momenta and all degrees",
        "tree_edges":TREE,
        "all_24_plaquette_edges":links.astype(int).tolist(),
        "all_24_plaquette_orientations":signs.astype(int).tolist(),
        "tree_gauge_remaining_edge_count":17,
        "selected_tree_plaquette_degree_profile":best,
        "exhaustive_spanning_tree_count":49152,
        "isotropic_tree_profile_dominance":dominance,
        "isotropic_product_trial":isotropic,
        "anisotropic_product_trial":anisotropic,
        "certified_log_Perron_lower":lower,
        "certified_Perron_lower":anisotropic["exponential_of_variational_bound"]["lower"],
        "proof_chain":["Positive character expansion gives C_beta >= |1><1|.",
                       "Hence T >= |s><s| and lambda0(T) >= integral exp((beta/3)D) dHaar.",
                       "Exact spanning-tree gauge fixing leaves seventeen independent Haar variables.",
                       "Jensen under product Wilson densities q_e gives log Z_sp >= beta sum_p product_(free e in p) r_e - sum_e(beta'_e r_e-log Z_e).",
                       "All r_e and log Z_e are certified by outward positive Bessel series, determinant sums, and infinite shift tails."],
        "not_claimed":["Exact Perron eigenvalue or normalized eigenfunction", "Global variational optimum", "Continuum or volume-uniform gap"],
        "sources":{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__), ROOT/"full_moments_v4/geometry.bin",ROOT/"dag_closeout_v5/certify_wilson.py",ROOT/"dag_closeout_v5/intervals.py"]},
    }
    (HERE/"GAUGE_FIXED_PERRON_LOWER_CERTIFICATE.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"log_lower":lower,"lambda_lower":result["certified_Perron_lower"],
                      "isotropic_log_lower":isotropic["variational_log_lower_bound"]},indent=2))


if __name__ == "__main__":
    main()
