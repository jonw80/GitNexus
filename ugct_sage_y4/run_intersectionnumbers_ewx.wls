(* UGCT Esole-Yau Ewx higher-Cartan exact-value driver

   Uses Jefferson-Turner arXiv:2206.11527 ancillary package
   sources/IntersectionNumbers.m.

   Real package API exposed by introspection:
     push[{a,4}, pushFunction -> f]
     divisors[{a,4}]
     hypersurface[{a,4}]

   For the split SU(5)/A4 Tate tuning, {a,4} is the standard A4 model.
   The package returns pushforwards to the base in terms of L and s[1].

   This script evaluates the final 235 higher-Cartan values:
     Dbase*C_i*C_j*C_k    for Dbase in {R,H,E1,...,E8}
     C_i*C_j*C_k*C_l

   and exports data/higher_cartan_closure_rules.json.
*)

SetDirectory[DirectoryName[$InputFileName]];
If[!DirectoryQ["reports"], CreateDirectory["reports"]];
If[!DirectoryQ["data"], CreateDirectory["data"]];

If[!FileExistsQ["sources/IntersectionNumbers.m"],
  report = <|"status" -> "INTERSECTIONNUMBERS_PACKAGE_MISSING", "missing" -> "sources/IntersectionNumbers.m"|>;
  Export["reports/intersectionnumbers_ewx_run_report.json", report, "JSON"];
  Print[ExportString[report, "JSON"]];
  Exit[0];
];

Get["sources/IntersectionNumbers.m"];

baseNames = {"R", "H", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"};
cartanNames = {"C1", "C2", "C3", "C4"};
baseVars = {r, h, e1, e2, e3, e4, e5, e6, e7, e8};
baseClassAssoc = AssociationThread[baseNames -> baseVars];

(* c1(B3)=2R+6H-2 Sum Ei, and the tuning/GUT divisor S is R. *)
Lclass = 2 r + 6 h - 2 Total[{e1, e2, e3, e4, e5, e6, e7, e8}];
Sclass = r;
baseSubstitution = {L -> Lclass, s[1] -> Sclass};

surfPair[x_, y_] := Which[
  x === h && y === h, 1,
  MemberQ[{e1,e2,e3,e4,e5,e6,e7,e8}, x] && x === y, -1,
  True, 0
];

kPair[x_] := Which[
  x === h, -3,
  MemberQ[{e1,e2,e3,e4,e5,e6,e7,e8}, x], -1,
  True, 0
];

kSquare = 1;

intExp[exps_List] := Module[{rct, surf, surfDegree, varlist = baseVars},
  rct = exps[[1]];
  surf = Rest[exps];
  surfDegree = Total[surf];
  Which[
    Total[exps] =!= 3, 0,
    rct == 0, 0,
    rct == 1 && surfDegree == 2,
      Module[{positions = Flatten[MapIndexed[ConstantArray[#2[[1]] + 1, #1] &, surf]]},
        If[Length[positions] =!= 2, 0, surfPair[varlist[[positions[[1]]]], varlist[[positions[[2]]]]]]
      ],
    rct == 2 && surfDegree == 1,
      Module[{pos = First@Flatten[MapIndexed[ConstantArray[#2[[1]] + 1, #1] &, surf]]}, kPair[varlist[[pos]]]],
    rct == 3 && surfDegree == 0, kSquare,
    True, 0
  ]
];

integrateB3[poly_] := Module[{rules, expanded},
  expanded = Expand[poly];
  rules = CoefficientRules[expanded, baseVars];
  Total[(#[[2]] intExp[#[[1]]]) & /@ rules]
];

jsonValue[x_] := ToString[InputForm[x]];
key[parts_List] := StringRiffle[SortBy[parts, Join[baseNames, cartanNames] /. Thread[Join[baseNames, cartanNames] -> Range[Length[Join[baseNames, cartanNames]]]] /. y_String :> 999], ","];

(* Safer canonical key order matching the Python/Sage validators. *)
orderAssoc = AssociationThread[Join[{"R","H"}, Table["E"<>ToString[i], {i,1,8}], {"Z"}, cartanNames] -> Range[15]];
ckey[parts_List] := StringRiffle[SortBy[parts, Lookup[orderAssoc, #, 999] &], ","];

runResult = Quiet@Check[
  cartanClasses = divisors[{a, 4}];
  If[Length[cartanClasses] =!= 4, Throw["Expected four A4 Cartan divisor classes from divisors[{a,4}]"]];

  pushBase[expr_] := Expand[push[{a, 4}, pushFunction -> expr] /. baseSubstitution];

  values = <||>;
  Do[
    dname = baseNames[[didx]];
    dclass = baseClassAssoc[dname];
    triples = Subsets[Range[4], {3}, Repetition -> True];
    Do[
      prod = Times @@ (cartanClasses[[#]] & /@ triple);
      val = integrateB3[dclass * pushBase[prod]];
      values[ckey[Join[{dname}, cartanNames[[triple]]]]] = jsonValue[val],
      {triple, triples}
    ],
    {didx, Length[baseNames]}
  ];

  quads = Subsets[Range[4], {4}, Repetition -> True];
  Do[
    prod = Times @@ (cartanClasses[[#]] & /@ quad);
    val = integrateB3[pushBase[prod]];
    values[ckey[cartanNames[[quad]]]] = jsonValue[val],
    {quad, quads}
  ];

  pkgHash = IntegerString[FileHash["sources/IntersectionNumbers.m", "SHA256"], 16, 64];
  scriptHash = IntegerString[FileHash[$InputFileName, "SHA256"], 16, 64];
  valueHash = IntegerString[Hash[Normal[values], "SHA256"], 16, 64];

  out = <|
    "schema_version" -> "UGCT_HIGHER_CARTAN_CLOSURE_RULES_V3",
    "status" -> "EXACT_EWX_SELF_INTERSECTION_TABLE_CERTIFIED",
    "resolution_chamber" -> "Esole-Yau Ewx / standard split SU(5) A4 Tate tuning via IntersectionNumbers.m",
    "exact_values" -> values,
    "fallback_rule" -> <|"enabled" -> False, "name" -> "NO_FALLBACK_FOR_CERTIFICATION"|>,
    "provenance" -> <|
      "toolchain" -> "WolframScript + Jefferson-Turner IntersectionNumbers.m",
      "toolchain_version" -> ToString[$Version],
      "source_geometry" -> "split SU(5)/A4 Tate model, package call push[{a,4}, pushFunction->...], GUT divisor S=s[1]=R, B3=P(O+K_dP8)",
      "sr_linear_ideal_hash" -> "sha256:" <> pkgHash,
      "proper_transform_hash" -> "sha256:" <> pkgHash,
      "script_hash" -> "sha256:" <> scriptHash,
      "independent_rerun_hash" -> "sha256:" <> valueHash
    |>,
    "computed_by" -> "run_intersectionnumbers_ewx.wls",
    "value_count" -> Length[values]
  |>;
  Export["data/higher_cartan_closure_rules.json", out, "JSON"];
  report = <|
    "status" -> "INTERSECTIONNUMBERS_EWX_EXACT_VALUES_EXPORTED",
    "value_count" -> Length[values],
    "package_hash" -> "sha256:" <> pkgHash,
    "script_hash" -> "sha256:" <> scriptHash,
    "value_hash" -> "sha256:" <> valueHash,
    "cartan_classes" -> ToString[InputForm[cartanClasses]],
    "output" -> "data/higher_cartan_closure_rules.json"
  |>;
  Export["reports/intersectionnumbers_ewx_run_report.json", report, "JSON"];
  Print[ExportString[report, "JSON"]];
  "OK",
  $Failed
];

If[runResult === $Failed,
  report = <|
    "status" -> "INTERSECTIONNUMBERS_EWX_EXACT_VALUES_FAILED",
    "message" -> "The package loaded, but the exact A4/SU(5) push call failed. Inspect Wolfram messages and reports/intersectionnumbers_api_introspection.md.",
    "expected_call" -> "push[{a,4}, pushFunction -> product_of_divisors[{a,4}]]"
  |>;
  Export["reports/intersectionnumbers_ewx_run_report.json", report, "JSON"];
  Print[ExportString[report, "JSON"]];
  Exit[0];
];

Exit[0];
