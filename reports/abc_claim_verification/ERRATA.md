# Verification report: "An Effective Proof of the ABC Conjecture with Explicit Bounds"

Every numerical and algebraic claim in the manuscript was checked. Reproduce with
`python3 verify_abc_paper.py` (requires `mpmath`).

**Result: the proof cannot be repaired.** Two separate steps are fatal, and neither is
an arithmetic slip:

- **Equation (1) is false.** An explicit infinite family of counterexamples is given below.
- **Lemma 2 assumes the ABC conjecture itself.**

Equation (1) is the only step in the entire manuscript that ever produces an upper bound
on `C`. Everything else either post-processes it or is unused. So there is no proof left
once it goes.

---

## A. Fatal errors

### A1. Equation (1) is both misattributed and false

The manuscript states, attributing it to Stewart–Yu (2001, Theorem 1):

```
log C  <=  (2/3) log r  +  33.3 (log r)^(1/3) (log log r)^(2/3)  +  10          (1)
```

with `r = rad(ABC)`.

**Misattribution.** Stewart and Yu, *On the abc conjecture, II*, **Duke Math. J. 108**
(2001), 169–181 — not *Math. Ann.*, which was their earlier 1991 paper (Math. Ann. 291,
225–230) — prove

```
log C  <=  kappa * r^(1/3) * (log r)^3
```

That bound is **polynomial in `r`**, not logarithmic. It gives `C < exp(kappa r^(1/3)(log r)^3)`,
which is astronomically weaker than `C < K_eps * r^(1+eps)` and yields nothing toward ABC.
No result of the shape (1) exists in the literature.

**Why it could not exist.** (1) asserts `C <= r^(2/3 + o(1))`. The ABC conjecture itself only
asserts `C <= r^(1+eps)`. So (1) is *strictly stronger than the theorem being proved* — it
is not a preliminary, it is a superweapon. Any argument that assumes it is circular at best.

**Explicit refutation.** For `N = 2^k` take

```
A = 1,   B = 3^N - 1,   C = 3^N
```

These are coprime, satisfy `A + B = C` and `C > max(A,B)`, so they are ABC triples under
Definition 1. By lifting-the-exponent,

```
v_2(3^(2^k) - 1) = v_2(3-1) + v_2(3+1) + v_2(2^k) - 1 = 1 + 2 + k - 1 = k + 2
```

(verified exactly on the integers for `k = 1..12` in the script). So `2^(k+2)` exactly divides `B`,
giving `rad(B) <= B / 2^(k+1)` and hence

```
rad(ABC) = 3 * rad(B) <= 3B / 2^(k+1)
```

The RHS of (1) is increasing in `log r`, so substituting an **upper** bound for `log r` yields an
**upper** bound for the RHS — the correct direction for a refutation.

At `k = 14` (`C = 3^16384`, a 7818-digit number), by exact integer arithmetic:

| quantity | value |
|---|---|
| `log C` | 17999.6637375 |
| `log r` (upper bound) | 17990.3651421 |
| Equation (1) RHS | 15998.7637925 |
| **`log C` − RHS** | **+2000.89994499** |

Equation (1) fails, and it fails for **every** `k >= 14`, with the margin growing without
bound (`+6728` at `k=15`, `+17069` at `k=16`, `+84107` at `k=18`). The mechanism: the gap
`log C − (2/3) log r` grows like `(1/3) log C`, i.e. linearly in `N`, while the correction term
`33.3 (log r)^(1/3)(log log r)^(2/3)` grows only like `N^(1/3)`. No choice of the constants
`33.3` and `10` can rescue it.

**Not repairable.** Substituting the true Stewart–Yu bound leaves Case 1 with
`log C <= kappa r^(1/3)(log r)^3`, which is superpolynomially too weak to give `r^(1+eps)`.

### A2. Lemma 2 is circular, and its proof is invalid

Lemma 2 claims `log rad(ABC) >= (1 - o(1)) log C`. Exponentiating: `C <= rad(ABC)^(1+o(1))`.
**That is the ABC conjecture.** It is being assumed as a lemma in its own proof.

The offered proof is independently unsound:

- Brun's sieve bounds the count of integers up to `x` with no small prime factor. It says
  nothing about the radical of one specific triple, and no sieve can — the statement is about
  an individual arithmetic object, not a density.
- The displayed inequality `S(x;P) <= x * sum_{d | prod P} mu(d)/d <= x/log log x + ...` is
  garbled. The Legendre/Brun main term is `x * prod_{p in P} (1 - 1/p)`, and the claimed
  further bound by `x/log log x` does not follow.
- `rad(ABC) <= C^(3/2)` is asserted with no justification; the trivial bound is
  `rad(ABC) <= ABC < C^3`.
- Decisively: an **upper** bound on `rad(ABC)` can never yield a **lower** bound on
  `log rad(ABC)`. The final line reverses the inequality direction.

The same family from A1 refutes the lemma's uniform reading directly.

---

## B. Genuine errors that *are* correctable

These were fixed/derived correctly below, but fixing them does not save the proof.

### B1. Equation (2) — the "error term" does not tend to zero

The manuscript writes Mertens' theorem with error term
`O( integral_2^x t^-1 exp(-0.2 sqrt(log t)) dt )`.

The manuscript's own evaluation of that integral is **correct**: substituting `u = log t`
then `v = sqrt(u)` gives `2 * e^(-ab)/a * (b + 1/a)` with `a = 0.2`, `b = sqrt(log 2)`,
which equals **49.3792** (the paper says "approximately 49.5" — accurate to 0.25%;
independent quadrature confirms 49.37919881).

But a quantity converging to **49.38 rather than 0 is not an error term.** Equation (2)
is therefore true-but-vacuous, and so is the consequence (3). On Example 1 the bound reads
`0.88599 <= 52.525` — a slack of 51.6, carrying no information.

**Correct statement** (Rosser–Schoenfeld, for `x >= 286`):

```
| sum_{p<=x} 1/p - log log x - M |  <=  1/(10 log^2 x) + 4/(15 log^3 x)
```

### B2. Sections 3 and 4 are never used

Neither (3) nor Lemma 2's "first moment" claim appears anywhere in the proof of Theorem 1,
which invokes only (1) and Lemma 3. The Mertens and sieve material is decorative.

### B3. Lemma 3's derivation is algebraically invalid

From `33.3 (log log r)^(2/3) / (log r)^(2/3) < eps/2` the correct conclusion is:

```
divide by log r  ->  33.3 (log L)^(2/3) / L^(2/3) < eps/2      (L = log r)
rearrange        ->  L / (log L)^(2/3) > 66.6/eps
raise to 3/2     ->  L / log L > (66.6/eps)^(3/2)              <-- CORRECT
```

The manuscript instead writes `L > (33.3/eps)^3 (log(33.3/eps))^2`, which **drops the factor
2** and **replaces the exponent 3/2 by 3**.

The stated threshold is still *sufficient* for small `eps`, but wildly loose:

| `eps` | correct `log M_eps` | paper's `log M_eps` | factor |
|---|---|---|---|
| 1 | 4581.7 | 453781.6 | 99× |
| 0.1 | 210685.8 | 1.2457e9 | 5913× |
| 0.01 | 8.6837e6 | 2.4291e12 | 279735× |

The overshoot is unbounded, and it feeds directly into Case 2, inflating the constant `K_eps`.

**Worse, Lemma 3 is false as stated for large `eps`:** its own threshold stops implying its
conclusion at `eps > 8.8431466`, and for `eps >= 33.3` we have `log(33.3/eps) <= 0` and `M_eps`
is degenerate. Theorem 1 claims "for every `eps > 0`", so this range is not negligible.

### B4. Example 2 fails its own lemma's hypothesis

With `eps = 0.1`: `log M_eps = 1.2457e9`, but the example takes `r = e^(10^6)`, i.e.
`log r = 1e6 < 1.2457e9`. So `r < M_eps` and **Lemma 3 does not apply to its own example.**
The conclusion holds anyway — which is itself evidence the threshold is derived wrongly.
Under the corrected threshold the example *is* certified: `L/log L = 72382 > 666^1.5 = 17187.4`.

Arithmetic slip in the same example: `33.3 * 100 * (13.8155)^(2/3) = 19173`, i.e. `1.92e4`,
not the stated `1.7e4`. (The stated RHS `5e4` is correct.)

### B5. Case 2's order estimate is wrong

From `r <= M_eps`, Equation (1) gives `log C <= (2/3) log M_eps + ... = O(eps^-3 (log(1/eps))^2)`,
**not** `O(1/eps^3)`. Measured ratio to `1/eps^3`: 8.3e5 at `eps=0.1`, 1.6e6 at `0.01`,
2.7e6 at `0.001` — growing like `(log(1/eps))^2`, confirming the missing factor.

Separately, `"=> C < exp(O(1/eps^3)) * r^(2/3)"` introduces a factor `r^(2/3)` that is
never derived; in Case 2 the bound on `C` is absolute and carries no `r`-dependence.

### B6. Section 7 verifies nothing

At `eps = 0.1`, `K_eps = exp(1e15)`. The claim `C < K_eps * 15042^1.1` therefore passes with
about `1e15` of slack in the logarithm (`log C = 15.68` vs `1e15`). **Every** triple with
`C < exp(1e15)` passes identically. This tests the size of `K_eps`, not the conjecture.

The chosen triple `2 + 3^10*109 = 23^5` is in fact the Reyssat example, the record-holder with
quality `log C / log r = 1.62991`. It is precisely the kind of triple that Equation (1)'s
`C <= r^(2/3+o(1))` claims becomes impossible — making it a poor advertisement for (1).

### B7. Minor

- Definition 1: `C > max(A,B)` is automatic from `A + B = C` with `A, B >= 1`; and "coprime"
  should be `gcd(A,B) = 1`, which then forces pairwise coprimality.
- Example 1: the sum is `0.88599` (stated `0.885` — fine); `rad = 15042` and `A+B=C` both verified.
- Baker (2007) is credited in the abstract and listed as [2] but is never used in any argument.
  de Weger [3] is never cited in the text at all.

---

## C. Bottom line

Correcting B1–B7 yields a cleaner manuscript with **no theorem in it**. The two load-bearing
steps are not fixable by adjusting constants:

- Equation (1) is false, with explicit counterexamples `(1, 3^N - 1, 3^N)` for `N = 2^k`, `k >= 14`.
- Lemma 2 is the ABC conjecture restated.

The ABC conjecture remains open. Any genuine effective proof must produce a bound of the shape
`log C <= (1 + eps) log r + O_eps(1)` from inputs that do not already presuppose it — which is
exactly the difficulty the manuscript's Equation (1) assumes away.

## Sources

- C. L. Stewart and Kunrui Yu, *On the abc conjecture, II*, Duke Math. J. **108** (2001), 169–181.
- C. L. Stewart and Kunrui Yu, *On the abc conjecture*, Math. Ann. **291** (1991), 225–230.
- J. B. Rosser and L. Schoenfeld, *Approximate formulas for some functions of prime numbers*,
  Illinois J. Math. **6** (1962), 64–94.
