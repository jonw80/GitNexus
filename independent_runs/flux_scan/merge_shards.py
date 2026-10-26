#!/usr/bin/env python3
"""Merge shard outputs of mass_free_scan.py and print the summary table."""
import glob, json, os, sys

src, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(os.path.join(src, "**", "shard_*.json"), recursive=True))
shards = [json.load(open(f)) for f in files]
assert shards, "no shard files found"
nsh = shards[0]["nshards"]
assert sorted(s["shard"] for s in shards) == list(range(nsh)), "missing shards"
total = shards[0]["n_candidates_total"]
assert sum(s["n_candidates_this_shard"] for s in shards) == total
merged = {"n_candidates_total": total, "nshards": nsh, "grid": shards[0].get("grid"), "variants": {}}
for key in shards[0]["variants"]:
    roots, printed = {}, {}
    for s in shards:
        roots.update(s["variants"][key]["roots"])
        printed.update(s["variants"][key]["printed"])
    merged["variants"][key] = {"n_with_root": len(roots), "roots": roots, "printed": printed}
json.dump(merged, open(out, "w"))
lines = ["| variant (parameters, D_z, branch) | candidates with a real attractor root | printed vectors with a root |",
         "|---|---|---|"]
for key, v in merged["variants"].items():
    hits = [g for g, d in sorted(v["printed"].items()) if d["z_roots"]]
    lines.append(f"| {key.replace('|', ' / ')} | {v['n_with_root']} of {total} | {', '.join('gen ' + g for g in hits) if hits else 'none'} |")
print("\n".join(lines))
summ = os.environ.get("GITHUB_STEP_SUMMARY")
if summ:
    with open(summ, "a") as fh:
        fh.write("## Mass-free flux scan (manuscript Definition: flux-admissible triple)\n\n" + "\n".join(lines) + "\n\n")
