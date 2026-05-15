(* UGCT Esole-Yau Ewx higher-Cartan exact-value driver

   Purpose:
     Use Jefferson-Turner arXiv:2206.11527 ancillary package
     sources/IntersectionNumbers.m to compute the final 235 higher-Cartan
     self-intersections for the split SU(5)/A4 Ewx chamber.

   Required output:
     data/higher_cartan_closure_rules.json

   Notes:
     This script is deliberately explicit about the local UGCT divisor names.
     The only package-specific part is the model-construction call in the
     section marked PACKAGE INVOCATION. If the installed IntersectionNumbers.m
     exposes a different symbol name than expected, the script emits the list
     of exported package symbols so the call can be adjusted without changing
     the certificate format.
*)

SetDirectory[DirectoryName[$InputFileName]];
Needs["GeneralUtilities`"];

If[!FileExistsQ["sources/IntersectionNumbers.m"],
  Print[ExportString[<|"status" -> "INTERSECTIONNUMBERS_PACKAGE_MISSING", "missing" -> "sources/IntersectionNumbers.m"|>, "JSON"]];
  Exit[0];
];

Get["sources/IntersectionNumbers.m"];

baseDivisors = {"R", "H", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"};
cartanDivisors = {"C1", "C2", "C3", "C4"};

requiredMonomials = Join[
  Flatten[Table[Prepend[Sort[{ci,cj,ck}], d], {d, baseDivisors}, {ci, cartanDivisors}, {cj, cartanDivisors}, {ck, cartanDivisors}], 2] // DeleteDuplicates,
  Subsets[cartanDivisors, {4}, Repetition -> True]
];
key[parts_] := StringRiffle[parts, ","];

(* Base intersection form for dP8 and B3=P(O+K_dP8). *)
surfPair[a_, b_] := Which[
  a == "H" && b == "H", 1,
  StringStartsQ[a, "E"] && a == b, -1,
  True, 0
];

(* PACKAGE INVOCATION

   The expected external package task is:
     1. construct the split SU(5) Tate model;
     2. select the Esole-Yau Ewx resolution chamber;
     3. declare the base divisor S=w as R;
     4. request the generating function/intersection table;
     5. evaluate each required monomial.

   Because the public package API may expose version-specific symbol names,
   this driver first checks for common exported symbols. If none are found, it
   writes a symbol inventory report rather than fabricating values.
*)

exportedSymbols = Names["IntersectionNumbers`*"];
knownConstructors = Select[exportedSymbols, StringContainsQ[#, "Tate" | "Intersection" | "Generating" | "Resolve" | "SU"] &];

If[Length[knownConstructors] == 0,
  report = <|
    "status" -> "INTERSECTIONNUMBERS_API_NOT_DETECTED",
    "exported_symbols" -> exportedSymbols,
    "message" -> "IntersectionNumbers.m loaded, but no Tate/intersection constructor symbols were detected. Open sources/Intersection-Number-Examples.nb and map the SU(5) Ewx call into this driver."
  |>;
  Export["reports/intersectionnumbers_ewx_run_report.json", report, "JSON"];
  Print[ExportString[report, "JSON"]];
  Exit[0];
];

(* The exact API call must be filled after inspecting Intersection-Number-Examples.nb.
   We keep this as a hard stop so no uncertified table is produced. *)
report = <|
  "status" -> "INTERSECTIONNUMBERS_DRIVER_READY_API_MAPPING_REQUIRED",
  "candidate_symbols" -> knownConstructors,
  "required_output_count" -> 235,
  "next_step" -> "Map the package's documented SU(5) Tate-model call to Esole-Yau Ewx, then compute requiredMonomials and export exact_values."
|>;
Export["reports/intersectionnumbers_ewx_run_report.json", report, "JSON"];
Print[ExportString[report, "JSON"]];
Exit[0];
