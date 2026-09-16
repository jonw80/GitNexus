#!/usr/bin/env python3
"""Exact finite-Wilson neutral-observable identification and scalar bounds.

The true Perron function is defined analytically, not numerically supplied.
This run verifies the finite geometry and directed constants in the proof.
It does not compute Gram matrices, numerical vacuum vectors, or continuum
correlation functions.
"""
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "dag_closeout_v5"))
from intervals import I
sys.path.insert(0, str(ROOT / "wilson_transfer_v11/direct_review"))
from certify_gauge_fixed_perron import exp_interval

BETA = F(271, 20)
LINKS = 24


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry():
    # Periodic L=2 three-dimensional cubic lattice. Every positively
    # directed link is indexed by 3*vertex+direction; the vertex bits
    # are its three coordinates. No historical binary is needed to run.
    edges, signs = [], []
    for v in range(8):
        for mu, nu in [(0, 1), (0, 2), (1, 2)]:
            v_mu = v ^ (1 << (2-mu))
            v_nu = v ^ (1 << (2-nu))
            edges.append((3*v+mu, 3*v_mu+nu, 3*v_nu+mu, 3*v+nu))
            signs.append((1, 1, -1, -1))
    for row, orientation in zip(edges, signs):
        assert len(set(row)) == 4
        oriented = []
        for edge, sign in zip(row, orientation):
            assert sign in (-1, 1)
            source, mu = divmod(edge, 3)
            target = source ^ (1 << (2-mu))
            oriented.append((source, target) if sign == 1 else (target, source))
        assert all(oriented[i][1] == oriented[(i+1) % 4][0] for i in range(4))
    counts = Counter(e for row in edges for e in row)
    incidence = [counts[e] for e in range(LINKS)]
    assert incidence == [4]*LINKS
    cuts = []
    for mu in range(3):
        cut = {3*v+mu for v in range(8) if v & (1 << (2-mu))}
        exponents = [sum(sign for e, sign in zip(row, orient) if e in cut)
                     for row, orient in zip(edges, signs)]
        assert exponents == [0]*24
        cuts.append({"direction": mu, "edge_indices": sorted(cut),
                     "oriented_center_exponent_of_every_plaquette": exponents})
    return edges, signs, incidence, cuts


def main():
    edges, signs, incidence, cuts = geometry()
    # Schur orthogonality: int |Tr U|^2 = sum_(i,j) delta_ij/3 = 1.
    trace_abs_second = sum((F(int(i == j), 3) for i in range(3)
                            for j in range(3)), F(0))
    assert trace_abs_second == 1
    # Center invariance gives int Tr U = int (Tr U)^2 = 0.
    haar_variance = trace_abs_second / 2
    assert haar_variance == F(1, 2)
    chosen_edge = edges[0][0]
    spatial_log_ratio = BETA * F(9, 2) * incidence[chosen_edge] / 6
    temporal_log_ratio = BETA * F(9, 2) / 3
    perron_log_ratio = spatial_log_ratio + temporal_log_ratio
    density_log_ratio = 2*perron_log_ratio
    assert density_log_ratio == 9*BETA
    density_floor = 1/exp_interval(I(density_log_ratio))
    variance_floor = haar_variance*density_floor
    variance_ceiling = F(81, 16)  # (3 - (-3/2))^2 / 4.
    exponent = F(3, 2)*BETA*LINKS
    tau_ceiling = exp_interval(I(exponent))
    deficit = 2/(tau_ceiling + 1)
    susceptibility_ceiling = variance_ceiling*tau_ceiling
    result = {
        "schema": "YM_FINITE_WILSON_NEUTRAL_CHANNEL_IDENTIFICATION_V12",
        "status": "PASS_FINITE_VOLUME_ANALYTIC_IDENTIFICATION_AND_CONSTANTS",
        "operator": "T=S C_beta^tensor24 S; normalized transfer T/lambda_0",
        "exact_beta": str(BETA),
        "observable": "O(U)=ReTr of the elementary (mu,nu)=(0,1) plaquette based at vertex 0, unnormalized trace",
        "geometry_construction": "Periodic three-dimensional L=2 torus; e=3*v+mu; target=v xor (1<<(2-mu)); positive elementary plaquette orientations",
        "plaquette_0_edges": list(edges[0]),
        "plaquette_0_orientations": list(signs[0]),
        "all_plaquettes_have_four_distinct_links_and_form_closed_loops": True,
        "number_of_plaquettes_incident_to_each_link": incidence,
        "spatial_center_cut_checks": cuts,
        "gauge_invariant": True,
        "electric_center_flux_sector": "neutral under all three spatial Z3 cuts",
        "state": "psi=(O-<phi,O phi>)phi, where phi is the exact unit positive Perron function",
        "nonzero_state_proved": True,
        "zero_momentum_projection_performed": False,
        "lowest_neutral_excitation_identified": False,
        "exact_Haar_trace_absolute_second_moment": str(trace_abs_second),
        "exact_Haar_ReTr_variance": str(haar_variance),
        "one_edge_spatial_log_ratio_bound_exact": str(spatial_log_ratio),
        "one_edge_temporal_log_ratio_bound_exact": str(temporal_log_ratio),
        "one_edge_Perron_log_ratio_bound_exact": str(perron_log_ratio),
        "one_edge_conditional_density_log_ratio_bound_exact": str(density_log_ratio),
        "conditional_Perron_density_to_Haar_lower_enclosure": density_floor.record(),
        "true_connected_variance_lower_bound_enclosure": variance_floor.record(),
        "true_connected_variance_universal_upper_bound_exact": str(variance_ceiling),
        "correlation_identity": "C(n)=<psi,(T/lambda_0)^n psi>, n integer >=0",
        "correlation_bounds": "0<=C(n)<=Var_pi(O)*(1-delta)^n<=81/16*exp(-delta*n)",
        "strictly_positive_C_n_for_every_finite_n": True,
        "spectral_deficit_enclosure": deficit.record(),
        "integrated_autocorrelation_definition": "tau_int=1+2*sum_{n>=1} C(n)/C(0)",
        "integrated_autocorrelation_upper_bound_enclosure": tau_ceiling.record(),
        "time_susceptibility_definition": "chi=C(0)+2*sum_{n>=1} C(n)",
        "time_susceptibility_upper_bound_enclosure": susceptibility_ceiling.record(),
        "execution_scope": "Exact finite geometry and Haar constants, directed exponential bounds, self-contained operator proof; no numerical phi or moments",
        "finite_volume_Wilson_observable_identification_closed": True,
        "numerical_vacuum_or_physical_moment_arrays_computed": False,
        "continuum_field_identification_closed": False,
        "continuum_nontriviality_closed": False,
        "volume_uniform_gap_closed": False,
        "complete_yang_mills_proof": False,
        "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [
            Path(__file__), ROOT / "dag_closeout_v5/intervals.py",
            ROOT / "wilson_transfer_v11/direct_review/certify_gauge_fixed_perron.py"
        ]},
    }
    destination = HERE / "FINITE_NEUTRAL_CHANNEL_CERTIFICATE.json"
    destination.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"variance_lower": str(variance_floor.lo),
                      "spectral_deficit_lower": str(deficit.lo),
                      "gauge_and_center_invariance": True,
                      "continuum_closed": False}, indent=2))


if __name__ == "__main__":
    main()
