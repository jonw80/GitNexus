"""Corrected implementation of the routines in UniversalNPHardSolver.pdf.

See MATH_REVIEW.md for the audit, and verify_math.py for the executable checks.

The headline claim of the source document -- a universal solver for NP-hard
problems -- is not implemented here, because it is not achievable with these
ingredients: Grover search is bounded below by Omega(sqrt(N)) oracle queries
(Bennett-Bernstein-Brassard-Vazirani 1997), which is exponential in the number
of variables, and QAOA carries no approximation guarantee at fixed depth. What
this package provides is a correct hybrid heuristic with honest cost accounting.
"""

from .solver import NPHardSolver, Solution

__all__ = ["NPHardSolver", "Solution"]
