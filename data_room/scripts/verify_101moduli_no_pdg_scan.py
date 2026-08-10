#!/usr/bin/env python3
"""Strict finite no-PDG audit for the manuscript's four monomial-type flux coordinates.

This script deliberately does not promote the 4-vector n_j to an H^3 flux class;
the manuscript does not supply that integral map. It verifies the printed
Euclidean tadpole candidate count and reports the source-defined scope.
"""
import itertools

rows=[v for v in itertools.product(range(-6,7), repeat=4) if sum(x*x for x in v)<=44]
print('candidate_count',len(rows))
assert len(rows)==9697
print('status','FOUR_COORDINATE_FINITE_SCAN_REPRODUCED')
print('full_GVW_uniqueness','NOT_CERTIFIED_WITHOUT_H3_MAP_SIGMA_AND_GLOBAL_PERIOD_CONTINUATION')
