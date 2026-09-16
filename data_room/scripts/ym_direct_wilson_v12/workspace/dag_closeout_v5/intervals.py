"""Directed Decimal intervals; endpoints are serialized as exact decimals."""
from decimal import Decimal as D, Context, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_EVEN
from fractions import Fraction
import math

PREC = 90
DOWN = Context(prec=PREC, rounding=ROUND_FLOOR)
UP = Context(prec=PREC, rounding=ROUND_CEILING)
NEAR = Context(prec=PREC, rounding=ROUND_HALF_EVEN)

class I:
    def __init__(self, lo, hi=None):
        if isinstance(lo, I):
            self.lo, self.hi = lo.lo, lo.hi
        elif isinstance(lo, Fraction):
            self.lo = DOWN.divide(D(lo.numerator), D(lo.denominator))
            self.hi = UP.divide(D(lo.numerator), D(lo.denominator))
        else:
            self.lo, self.hi = D(lo), D(lo if hi is None else hi)
        if self.lo > self.hi or not self.lo.is_finite() or not self.hi.is_finite():
            raise ArithmeticError('invalid finite interval')
    def __add__(self, other):
        o=I(other); return I(DOWN.add(self.lo,o.lo), UP.add(self.hi,o.hi))
    __radd__=__add__
    def __neg__(self): return I(self.hi.copy_negate(), self.lo.copy_negate())
    def __sub__(self, other): return self+-I(other)
    def __rsub__(self, other): return I(other)+-self
    def __mul__(self, other):
        o=I(other); ps=[(a,b) for a in (self.lo,self.hi) for b in (o.lo,o.hi)]
        return I(min(DOWN.multiply(a,b) for a,b in ps),max(UP.multiply(a,b) for a,b in ps))
    __rmul__=__mul__
    def __truediv__(self, other):
        o=I(other)
        if o.lo<=0<=o.hi: raise ArithmeticError('division through zero')
        return self*I(DOWN.divide(D(1),o.hi),UP.divide(D(1),o.lo))
    def __rtruediv__(self, other): return I(other)/self
    def __pow__(self,n):
        if not isinstance(n,int) or n<0: raise ValueError(n)
        v=I(1); x=self
        while n:
            if n&1:v=v*x
            x=x*x;n//=2
        return v
    def sqrt(self):
        if self.lo<0:raise ArithmeticError('negative sqrt')
        a=NEAR.sqrt(self.lo);b=NEAR.sqrt(self.hi)
        return I(max(D(0),DOWN.next_minus(a)),UP.next_plus(b))
    def log(self):
        if self.lo<=0:raise ArithmeticError('nonpositive log')
        return I(DOWN.next_minus(NEAR.ln(self.lo)),UP.next_plus(NEAR.ln(self.hi)))
    def abs_upper(self):return max(self.lo.copy_abs(),self.hi.copy_abs())
    def record(self):return {'lower':str(self.lo),'upper':str(self.hi)}
    def floats(self):
        a=float(self.lo);b=float(self.hi)
        while D(a)>self.lo:a=math.nextafter(a,-math.inf)
        while D(b)<self.hi:b=math.nextafter(b,math.inf)
        return a,b

def rational_record(r):
    return I(Fraction(int(r['exact_numerator']),int(r['exact_denominator'])))

def gamma(n):
    return I(Fraction(n,2**53-n))
