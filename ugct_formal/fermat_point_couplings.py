#!/usr/bin/env python3
"""Weil-Petersson metric and normalized Yukawa coupling of the Fermat quintic,
computed from the Picard-Fuchs equation of X_5 alone.  No physical input, no
fitted number.

Family: the Dwork pencil  X_u = { x1^5+...+x5^5 - u*x1*x2*x3*x4*x5 = 0 } in P^4,
u = 5*psi.  u = 0 is the Fermat quintic X_5.  z = u^(-5).

Inputs (all mathematics):
  * Picard-Fuchs operator  theta^4 - 5z(5theta+1)(5theta+2)(5theta+3)(5theta+4)
    (Griffiths-Dwork reduction; Candelas-de la Ossa-Green-Parkes 1991).
  * Hodge theory: e^{-K} = i Int Omega ^ conj(Omega),  Yukawa = Int Omega ^ d^3 Omega,
    both monodromy invariant; the periods carry a real (integral) structure.
  * Irreducibility of the hypergeometric monodromy group (Beukers-Heckman 1989),
    which makes every invariant form unique up to a scalar.

Method:
  1. Local solutions at u = 0:  s_k(u) = sum_{m = k mod 5} a_m u^m,
     a_m = Gamma(m/5) / (Gamma(m) Gamma(1-m/5)^4),   k = 1..4.
  2. Conifold monodromy M_c: integrate the ODE once around z_c = 5^-5.
  3. Solve  M^+ D M = D  (D diagonal: the Z_5 monodromy at u = 0 has distinct
     eigenvalues),  M^T S M = S,  M R = R conj(M) with R conj(R) = 1.
     Check that  i R^T S  is proportional to D (the Hodge-theoretic link).
  4. Outputs at u = 0:  g_{u ubar}(0)  and  kappa_hat = |kappa| e^K g^(-3/2).
     Control: near large complex structure the same invariant must equal the classical
     formula built from the intersection number 5 and the Euler number chi(X_5) = -200
     (Candelas et al. 1991); inverting it returns chi from the monodromy computation.

Usage:  python3 -I fermat_point_couplings.py [digits]
"""
import sys
from mpmath import mp, mpf, mpc, gamma, pi, sqrt, exp, log, matrix, conj, fabs, nstr, svd_c, svd_r, binomial, zeta, findroot

mp.dps = int(sys.argv[1]) if len(sys.argv) > 1 else 45
zc = mpf(1) / 3125

# Picard-Fuchs in d/dz:  sum_i P_i(z) w^(i) = 0
P = [[-120], [1, -15000], [0, 7, -45000], [0, 0, 6, -25000], [0, 0, 0, 1, -3125]]


def shifted(poly, z0):
    """coefficients of poly(z0 + h) in powers of h"""
    out = [mpc(0)] * len(poly)
    for n, c in enumerate(poly):
        for r in range(n + 1):
            out[r] += c * binomial(n, r) * z0 ** (n - r)
    return out


def step(z0, w, h):
    """w = [w, w', w'', w'''] at z0  ->  same at z0 + h  (Taylor series of the ODE solution)"""
    Ps = [shifted(p, z0) for p in P]
    c = [w[0], w[1], w[2] / 2, w[3] / 6]
    tol = mpf(10) ** (-mp.dps - 8)
    n = 0
    while True:
        s = mpc(0)
        for i in range(5):
            for r, pr in enumerate(Ps[i]):
                if i == 4 and r == 0:
                    continue
                j = n - r + i
                if n - r < 0 or j < 0:
                    continue
                ff = mpf(1)
                for t in range(i):
                    ff *= (j - t)
                s += pr * c[j] * ff
        ff4 = mpf((n + 1) * (n + 2) * (n + 3) * (n + 4))
        c.append(-s / (Ps[4][0] * ff4))
        n += 1
        if n > 40 and max(abs(c[-k]) * abs(h) ** (len(c) - k) for k in range(1, 5)) < tol:
            break
    out = []
    for d in range(4):
        acc = mpc(0)
        for j in range(d, len(c)):
            ff = mpf(1)
            for t in range(d):
                ff *= (j - t)
            acc += c[j] * ff * h ** (j - d)
        out.append(acc)
    return out


def transport(path, W):
    """carry each row of W (a solution) along the polyline path"""
    W = [list(r) for r in W]
    for a, b in zip(path[:-1], path[1:]):
        W = [step(a, r, b - a) for r in W]
    return W


def a_coeffs(mmax):
    a = {}
    for k in range(1, 5):
        a[k] = gamma(mpf(k) / 5) / (gamma(k) * gamma(1 - mpf(k) / 5) ** 4)
        m = k
        while m + 5 <= mmax:
            a[m + 5] = a[m] * mpf(m) ** 4 / (mpf(5) ** 5 * (m + 1) * (m + 2) * (m + 3) * (m + 4))
            m += 5
    return a


def lg_wronskian(z):
    """rows k=1..4: (s_k, s_k', s_k'', s_k''') at z, from the u-series (|z| > z_c)"""
    u = z ** (-mpf(1) / 5)
    mmax = int(30 + (mp.dps + 10) * log(10) / (-log(abs(u) / 5)))
    a = a_coeffs(mmax)
    rows = []
    for k in range(1, 5):
        th = [mpc(0)] * 4                     # theta^j s_k,  theta = -(u/5) d/du
        for m in range(k, mmax + 1, 5):
            t = a[m] * u ** m
            for j in range(4):
                th[j] += t * (-mpf(m) / 5) ** j
        w1 = th[1] / z
        w2 = (th[2] - th[1]) / z ** 2
        w3 = (th[3] - 3 * th[2] + 2 * th[1]) / z ** 3
        rows.append([th[0], w1, w2, w3])
    return rows, a


def nullspace_real(rows_c, n):
    """real vector x (length n) with sum_j A_ij x_j = 0 for complex rows A"""
    A = matrix(2 * len(rows_c), n)
    for i, r in enumerate(rows_c):
        for j in range(n):
            A[2 * i, j] = r[j].real
            A[2 * i + 1, j] = r[j].imag
    U, Sv, V = svd_r(A)
    i0 = min(range(n), key=lambda i: Sv[i])
    return [V[i0, j] for j in range(n)], sorted(Sv, reverse=True)


def nullspace_complex(rows_c, n):
    A = matrix(len(rows_c), n)
    for i, r in enumerate(rows_c):
        for j in range(n):
            A[i, j] = r[j]
    U, Sv, V = svd_c(A)
    i0 = min(range(n), key=lambda i: Sv[i])
    return [conj(V[i0, j]) for j in range(n)], sorted(Sv, reverse=True)


def gam(x):
    return gamma(x) / gamma(1 - x)


def main():
    print(f"precision: {mp.dps} digits")
    r = mpf(6) / 10 * zc
    zb = zc + r
    W0, a = lg_wronskian(zb)
    N = 64
    loop = [zc + r * exp(2j * pi * mpf(j) / N) for j in range(N + 1)]
    W1 = transport(loop, W0)
    M = matrix(W1) * matrix(W0) ** -1          # row-solution convention: s -> M s
    E = M - mp.eye(4)
    sv = svd_c(E, compute_uv=False)
    print("conifold monodromy minus 1, singular values:", [nstr(x, 3) for x in sv])

    # Hermitian form D (diagonal) with M^+ D M = D
    eqs = []
    for i in range(4):
        for j in range(4):
            eqs.append([conj(M[k, i]) * M[k, j] - (1 if (k == i and i == j) else 0) for k in range(4)])
    d, svD = nullspace_real(eqs, 4)
    if d[0] < 0:
        d = [-x for x in d]
    print("D null-space singular values (last should be ~0):", [nstr(x, 3) for x in svD])
    print("D signs:", ["+" if x > 0 else "-" for x in d])

    # symplectic form S (S14 = -S41 = x, S23 = -S32 = y) with M^T S M = S
    def Smat(x, y):
        S = matrix(4, 4)
        S[0, 3], S[3, 0], S[1, 2], S[2, 1] = x, -x, y, -y
        return S
    eqs = []
    B1, B2 = Smat(1, 0), Smat(0, 1)
    T1 = M.T * B1 * M - B1
    T2 = M.T * B2 * M - B2
    for i in range(4):
        for j in range(4):
            eqs.append([T1[i, j], T2[i, j]])
    (x, y), svS = nullspace_complex(eqs, 2)
    S = Smat(x, y)

    # real structure R (anti-diagonal) with M R = R conj(M), R conj(R) = 1
    idx = [(0, 3), (1, 2), (2, 1), (3, 0)]
    eqs = []
    Mb = matrix([[conj(M[i, j]) for j in range(4)] for i in range(4)])
    for i in range(4):
        for j in range(4):
            row = []
            for (p, q) in idx:
                Rb = matrix(4, 4)
                Rb[p, q] = 1
                T = M * Rb - Rb * Mb
                row.append(T[i, j])
            eqs.append(row)
    rv, svR = nullspace_complex(eqs, 4)
    R = matrix(4, 4)
    for (p, q), v in zip(idx, rv):
        R[p, q] = v
    lam2 = (R * matrix([[conj(R[i, j]) for j in range(4)] for i in range(4)]))[0, 0]
    print("R conj(R) before scaling (must be real > 0):", nstr(lam2, 8))
    R = R / sqrt(lam2.real)
    RRb = R * matrix([[conj(R[i, j]) for j in range(4)] for i in range(4)])
    print("R conj(R) - 1, max entry:", nstr(max(abs(RRb[i, j] - (1 if i == j else 0)) for i in range(4) for j in range(4)), 3))

    # Hodge link: i R^T S must be proportional to D
    X = 1j * R.T * S
    off = max(abs(X[i, j]) for i in range(4) for j in range(4) if i != j)
    ratios = [X[k, k] / d[k] for k in range(4)]
    spread = max(abs(q / ratios[0] - 1) for q in ratios)
    print("i R^T S vs D: off-diagonal", nstr(off, 3), " ratio spread", nstr(spread, 3))
    c = ratios[0]
    S = S / c                      # now D = i R^T S exactly (fixes the joint phase/scale)

    # ---- outputs at the Fermat point u = 0 (Fermat gauge sigma_k = s_k / u) ----
    g_uu = -d[1] * abs(a[2]) ** 2 / (d[0] * abs(a[1]) ** 2)
    kappa0 = 6 * S[0, 3] * a[1] * a[4]          # Yukawa  sigma^T S d_u^3 sigma  at u = 0
    eK = 1 / (d[0] * abs(a[1]) ** 2)
    khat0 = abs(kappa0) * eK * g_uu ** (-mpf(3) / 2)
    pred_g = (gam(mpf(2) / 5) / gam(mpf(1) / 5)) ** 5
    kap = sqrt(gam(mpf(1) / 5) / gam(mpf(2) / 5) ** 3)      # Distler-Greene / tt* factor
    print()
    print("g_{u ubar}(0)                  =", nstr(g_uu, 30))
    print("(gamma(2/5)/gamma(1/5))^5      =", nstr(pred_g, 30))
    print("g_{psi psibar}(0) = 25 g_uu    =", nstr(25 * g_uu, 30))
    print("normalized Yukawa at u = 0     =", nstr(khat0, 30))
    print("kappa^5, kappa^2 = gamma(1/5)/gamma(2/5)^3 :", nstr(kap ** 5, 30))
    print("relative differences:", nstr(g_uu / pred_g - 1, 3), nstr(khat0 / kap ** 5 - 1, 3))

    # ---- control: same invariant near large complex structure ----
    rr = zb
    arc = [rr * exp(1j * pi * mpf(j) / 24) for j in range(25)]
    zL = -mpf(10) ** -14
    ray, zz = [], -rr
    while abs(zz) > abs(zL) * 1.0001:
        ray.append(zz)
        zz = zz * mpf(6) / 10
    ray += [zL]
    WL = transport(arc + ray[1:], W0)
    s = matrix([w[0] for w in WL]); s1 = matrix([w[1] for w in WL]); s3 = matrix([w[3] for w in WL])
    Dm = mp.diag(d)
    Nn = (s.H * Dm * s)[0, 0].real
    cross = (s.H * Dm * s1)[0, 0]
    g_zz = (abs(cross) ** 2 - Nn * (s1.H * Dm * s1)[0, 0].real) / Nn ** 2
    kz = (s.T * S * s3)[0, 0]
    khatL = abs(kz) / Nn / g_zz ** (mpf(3) / 2)
    print()
    y = -log(abs(zL)) / (2 * pi)                 # Im t; mirror-map and instanton terms ~1e-11 here
    A = mpf(20) / 3                              # (4/3) * (H^3 = 5)

    def khat_classical(chi):
        B = -chi * zeta(3) / (4 * pi ** 3)
        f = A * y ** 3 + B
        return 5 * 8 * f ** 2 / (3 * A ** 2 * y ** 4 - 6 * A * B * y) ** (mpf(3) / 2)

    chi_inv = findroot(lambda c: khat_classical(c) - khatL, -100)
    print(f"control at z = {nstr(zL, 3)} (Im t = {nstr(y, 6)}):")
    print("  normalized Yukawa from monodromy  =", nstr(khatL, 20))
    print("  classical formula, H^3=5, chi=-200 =", nstr(khat_classical(-200), 20))
    print("  2/sqrt(3) (leading term)           =", nstr(2 / sqrt(3), 20))
    print("  chi recovered by inverting formula =", nstr(chi_inv, 15))

    tol = mpf(10) ** (-(mp.dps - 10))
    ok = (abs(g_uu / pred_g - 1) < tol and abs(khat0 / kap ** 5 - 1) < tol
          and abs(chi_inv + 200) < mpf(10) ** -6 and spread < tol and off < tol)
    print()
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
