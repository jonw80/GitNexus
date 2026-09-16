# All-factor Haar reduction and contraction schedule

This calculation retains all 24 plaquette factors of the V15 Gram operator. It performs seven gauge integrations exactly and gives a verified compressed interaction graph for the remaining integral. It does **not** evaluate the remaining seventeen group integrations or the full Gram matrix.

## Exact removal of seven Haar variables

Let the spatial graph have eight vertices and 24 positively oriented links, including distinct periodic parallel links. Normalize Haar measure on SU(3) to mass one. Choose the spanning tree with edge IDs

`[0, 1, 4, 11, 13, 16, 20]`.

Fix a root vertex. Every link configuration can be written uniquely in the form

U_e = g_source(e) V_e g_target(e)^(-1),

with the root gauge element equal to identity and V_e=identity on every tree edge. Solve for the other seven gauge elements recursively along the tree. Conditional left/right Haar invariance proves that the change of variables sends the product of the 24 link Haar measures to the product of seven vertex Haar measures and seventeen non-tree-link Haar measures. A gauge-invariant integrand is independent of the vertex elements, so their seven integrations equal one exactly.

Every Gram entry of the stated physical Peter–Weyl basis is gauge invariant: both external functions and every plaquette weight are invariant. Therefore this applies to the **full** physical Gram entry, with all 24 weights present. The resulting 24 cyclic plaquette words are listed with their orientations in ALL_FACTOR_NETWORK_ANALYSIS.json. Tree letters are deleted because V_e=identity; non-tree letters are not reordered.

Global conjugation of the seventeen residual variables remains. One must not remove a further Haar variable without correctly handling stabilizers and a different integration measure.

## Verified separator schedule

Make one variable for each non-tree link and connect two variables when they appear in the same plaquette factor. The supplied elimination order has at most eight later neighbors per eliminated variable; its largest elimination bag has nine variables. This is an upper bound of eight on the primal graph treewidth, not a claim that every Fourier tensor has bond dimension eight. A minor-minimum-degree calculation gives a lower bound of seven. The corresponding ungauged schedule found has width sixteen, with a minor lower bound of ten. The search is seeded and reproducible, over 2,048 spanning trees; optimality is not asserted.

For a scalar vacuum Gram entry, at each elimination step gather every factor that contains the link U, multiply them, Haar-integrate U, and return the resulting separator factor. Subsequent factor scopes lie inside the listed bags. This is an exact Fubini prescription on a compact probability space. It includes every plaquette exactly once. Basis insertions for general entries must also be included; for spin-network external states their representation tensors and vertex intertwiners need their own contraction schedule. The scalar primal-graph width does not certify the cost of the complete open Gram tensor.

## Local polynomial sizes and remaining work

Each squared weight has polynomial degree 466 in fundamental and conjugate-fundamental matrix entries. Four action plaquettes meet each surviving original link. Adding both cutoff-292 external basis insertions gives the safe linkwise polynomial-degree bound

4*466 + 2*292 = 2448.

The full ambient SU(3) Fourier polynomial space through that degree has dimension

sum_{p+q<=2448} [(p+1)(q+1)(p+q+2)/2]^2
= 1354460215352146949538625.

This number is a complete ambient-space dimension, **not** a proved lower bound on optimally compressed tensors. Fusion, intertwiner sparsity, symmetries, singular-value compression and different elimination schedules may reduce practical cost. The graph schedule itself therefore does not settle feasibility.

The concrete next executor should store factors in a sparse representation/intertwiner basis, integrate the first scheduled link using its invariant projector, and report the number of nonzero blocks and certified discarded norm. An exact implementation must account for all invariant multiplicities. A numerical truncation must carry an outward norm error through multiplication and all remaining integrals; uncertified rank truncation is insufficient. No such contracted first-link tensor for the 466-degree full factors has been produced by this network-analysis calculation.

## Scope of the certificate

Proved/executed: the seven gauge integrations, 24 retained oriented factor words, complete graph elimination order, induced-width upper bound, minor lower bound, and ambient degree count. Open: the seventeen remaining coupled group integrations, all full Gram entries, and a useful certified tensor compression error. No lower-bound matrix is substituted for the requested integral.
