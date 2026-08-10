#!/usr/bin/env python3
"""
UGCT Fermat-quintic 101-direction period/derivative engine.

Exact source-defined scope:
  * 204 ordered CM characters a_i in {1,2,3,4}, sum a_i = 0 mod 5
  * 101 degree-5 monomials b_i <= 3
  * omega(a) = (1/5) prod Gamma(a_i/5)
  * first derivative coefficient c(a,b) from the printed Griffiths-Dwork residue formula.

This constructs the complete Fermat-point period vector and first-derivative
tensor. It intentionally does not claim a global nonlinear 101-moduli GVW solve.
"""
import itertools
import mpmath as mp
mp.mp.dps = 80

def characters():
    return [a for a in itertools.product(range(1,5), repeat=5) if sum(a) % 5 == 0]

def monomials():
    return [b for b in itertools.product(range(4), repeat=5) if sum(b) == 5]

def omega(a):
    out = mp.mpf(1)/5
    for ai in a:
        out *= mp.gamma(mp.mpf(ai)/5)
    return out

def coupling(a,b):
    shifted = tuple((ai+bi) % 5 for ai,bi in zip(a,b))
    if any(x == 0 for x in shifted):
        return mp.mpf('0')
    if sum(ai+bi for ai,bi in zip(a,b)) % 5:
        return mp.mpf('0')
    out = mp.mpf(1)
    for ai,si in zip(a,shifted):
        out *= mp.gamma(mp.mpf(si)/5) / mp.gamma(mp.mpf(ai)/5)
    return out

def build():
    A=characters(); B=monomials()
    Pi=[omega(a) for a in A]
    J=[[coupling(a,b) for b in B] for a in A]
    return A,B,Pi,J

if __name__ == '__main__':
    A,B,Pi,J=build()
    print('characters',len(A))
    print('moduli',len(B))
    print('jacobian_shape',len(J),len(J[0]))
