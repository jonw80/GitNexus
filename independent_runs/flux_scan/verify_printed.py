"""Independent high-precision check (mpmath, 30 digits) that the printed vectors have no real
attractor root, and the value of D_zW at the March-20 'best z*' points."""
import mpmath as mp
mp.mp.dps = 30
MT = [(0,0,0,2,3),(0,0,1,1,3),(0,0,1,2,2),(0,1,1,1,2)]
PRINTED = {3: (-1,3,2,5), 2: (2,2,5,-2), 1: (1,-2,-3,-3)}
ZSTAR = {3: mp.mpf('1.855592e-05'), 2: mp.mpf('1.647039e-05'), 1: mp.mpf('1e-10')}
def wF(a): return mp.fprod(mp.gamma(mp.mpf(v)/5) for v in a)/5
def prm(a, var): s = sorted(a); return [mp.mpf(v)/5 for v in (s[:4] if var=='first4' else s[1:])]
def F(p, x): return mp.hyper(p, [1,1,1], x)
def dF(p, x): return mp.fprod(p)*mp.hyper([q+1 for q in p], [2,2,2], x)
P0 = [mp.mpf(k)/5 for k in (1,2,3,4)]
def g(n, x, var, eq):
    s = mp.mpf(0)
    L = dF(P0, x)/F(P0, x)
    for nm, b in zip(n, MT):
        a = tuple(bi+1 for bi in b); p = prm(a, var); w = wF(a)
        s += nm*w*(dF(p, x) - (L*F(p, x) if eq == 'kahler' else 0))
    return s
xs = [-0.999 + 1.998*k/400 for k in range(401)]
xs = [x for x in xs if abs(x) > 1e-9] + [1e-12, -1e-12, 1e-8, -1e-8, 1e-5, -1e-5, 1e-3, -1e-3]
xs = sorted(xs)
for var in ('first4', 'last4'):
    for eq in ('flat', 'kahler'):
        for gen, n in PRINTED.items():
            vals = [g(n, mp.mpf(x), var, eq) for x in xs]
            signs = {int(mp.sign(v)) for v in vals}
            vmin = min(abs(v) for v in vals)
            at = g(n, 3125*ZSTAR[gen], var, eq)
            print(f"{var:6s} {eq:6s} gen{gen} n={n}: sign(D_xW) on [-0.999,0.999] = {sorted(signs)}  min|D_xW| = {mp.nstr(vmin,4)}  D_xW at March-20 z* = {mp.nstr(at,6)}")
