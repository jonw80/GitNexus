"""Clause (iv): hierarchy preservation over all ordered triples (n3, n2, n1) whose members each have a
real attractor root (clauses i-iii). Y_f = |omega_f(0) F_f(x*)|^2 eta_f (hypergeometric deformation map)."""
import json, sys, ast, itertools, numpy as np
import mass_free_scan as m
res = json.load(open(sys.argv[1]))
out = {}
for key, v in res['variants'].items():
    var, eq, br = key.split('|')
    S = [(tuple(ast.literal_eval(k)), r[0]) for k, r in v['roots'].items()]      # first root of each candidate
    if not S:
        out[key] = {'admissible_vectors': 0, 'admissible_triples': 0}; continue
    xs = np.array([x for _, x in S])
    Y = {f: np.array([m.yukawa(f, x, var) for x in xs]) for f in m.FERMION}
    total = 0
    # count ordered triples (i3, i2, i1) with Y_u[i1] < Y_c[i2] < Y_t[i3], Y_d[i1] < Y_s[i2] < Y_b[i3], Y_e[i1] < Y_mu[i2] < Y_tau[i3]
    ok3 = lambda i3: True
    n = len(S)
    cnt = 0
    for i2 in range(n):
        lo1 = (Y['u'] < Y['c'][i2]) & (Y['d'] < Y['s'][i2]) & (Y['e'] < Y['mu'][i2])
        hi3 = (Y['t'] > Y['c'][i2]) & (Y['b'] > Y['s'][i2]) & (Y['tau'] > Y['mu'][i2])
        cnt += int(lo1.sum()) * int(hi3.sum())
    rng = {f: (float(Y[f].min()), float(Y[f].max())) for f in Y}
    out[key] = {'admissible_vectors': n, 'admissible_triples': cnt, 'all_triples': n**3,
                'Yukawa_range_over_roots': rng}
    print(f"{key:26s} vectors with a root {n:4d}  triples passing (iv) {cnt:>12,d} of {n**3:>12,d}")
json.dump(out, open(sys.argv[2], 'w'), indent=1)
