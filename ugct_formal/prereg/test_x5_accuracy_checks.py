"""Unit tests of x5_dictionary.py and x5_accuracy_scan.py on planted inputs, without running the scans.
python3 -I test_x5_accuracy_checks.py   (exits 1 on a failed test; needs numpy, mpmath, cypari2)
"""
import importlib.util
import os

import numpy as np
from mpmath import mp, mpf, pi, log, exp

mp.dps = 50
here = os.path.dirname(os.path.abspath(__file__))


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


xd, xs = load("x5_dictionary"), load("x5_accuracy_scan")

# --- dictionary: recomputations from X_5's defining data
assert xd.chern_numbers() == (50, -200)
assert xd.h21_from_monomials() == 101
assert xd.characters() == (204, 51)
assert xd.gopakumar_vafa(4) == [2875, 609250, 317206375]
counts = {p: xd.dwork_point_count(p) for p in (2, 3, 7, 13, 17)}
assert counts[2] == 16 and counts[3] == 36

# --- conifold newform identification, and its failure on corrupted data
import cypari2
pari = cypari2.Pari()
forms = [[int(c) for c in pari(f"mfcoefs(mfeigenbasis(mfinit([25, 4], 0))[{j}], 20)")] for j in (1, 2, 3)]
assert xd.fit_forms(counts, forms) == [(1, 1)]
bad = dict(counts)
bad[7] += 1
assert xd.fit_forms(bad, forms) == []
wrong = [list(c) for c in forms]
for c in wrong:
    c[3] = -c[3]
assert all(a2 != 1 for a2, _ in xd.fit_forms(counts, wrong))

# --- relative windows
lo, hi = xs.rel_window(mpf("0.5"))
assert abs(lo - float(log(0.5))) < 1e-15 and abs(hi - float(log(1.5))) < 1e-15
sv = np.array([0.0, 1.0, 2.0])
assert list(xs.window_hits(sv, np.array([1.0, 1.5]), -1e-12, 1e-12)) == [1, 0]

# --- family B on a planted dictionary: decoder, values, planted hit, window count = verified count
ent = [{"name": str(v), "value": mpf(v)} for v in (2, 3, 7, 11)]
core, decode = xs.family_b_core([float(log(e["value"])) for e in ent])
vb = xs.family_b(core)
assert len(vb) == xs.family_b_size(4) == 7735
for f in range(len(vb)):
    v = xs.value_b(ent, decode(f // 7), int(xs.PI_EXPS[f % 7]))
    assert abs(exp(vb[f]) / v - 1) < 1e-12, f
T = mpf(2) ** 2 * mpf(3) ** -1 * mpf(7) ** 3 * pi
n_ok, distinct = xs.scan_b(ent, vb, decode, T, T * mpf("1e-30"))
assert n_ok >= 1 and any(abs(v - T) < mpf(10) ** -40 for _, v in distinct)
assert any(set(lab.split(" * ")) == {"pi^1", "2^2", "3^-1", "7^3"} for lab, _ in distinct)
n_off, _ = xs.scan_b(ent, vb, decode, T * (1 + mpf("1e-9")), T * mpf("1e-11"))
assert n_off == 0
sb = np.sort(vb)
rng = np.random.default_rng(1)
for t in np.exp(rng.uniform(0, 8, 25)):
    tt = mpf(float(t))
    tol = tt * mpf("3e-3")
    l, h = xs.rel_window(tol / tt)
    n_v, _ = xs.scan_b(ent, vb, decode, tt, tol)
    assert n_v == int(xs.window_hits(sb, np.array([float(log(tt))]), l, h)[0]), t

# --- family A: planted X_5-type hit, reference hit, and a miss
ent2 = [{"name": "2", "value": mpf(2)}, {"name": "3", "value": mpf(3)}]
al = 1 / mpf(137)
t1 = mpf(3) ** -1 * al ** 2 * pi ** -1
hits, cnt, _, _ = xs.scan_a(ent2, al, t1, t1 * mpf("1e-12"))
assert [(h[0], h[1], h[2], h[3]) for h in hits] == [(1, -1, 2, -1)] and cnt == 1
t2 = al ** 2 / pi
hits, cnt, _, _ = xs.scan_a(ent2, al, t2, t2 * mpf("1e-12"))
assert [(h[0], h[2], h[3]) for h in hits] == [(-1, 2, -1)] and cnt == 0
hits, cnt, _, _ = xs.scan_a(ent2, al, t1 * mpf("1.01"), t1 * mpf("1e-6"))
assert hits == [] and cnt == 0

print("x5 accuracy checks: all tests passed")
