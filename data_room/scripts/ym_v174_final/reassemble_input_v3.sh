#!/usr/bin/env bash
# Extracted verbatim from ym-v174-final-external-reduction.yml so both phases
# reassemble input_v3 identically, including the single-character repair path
# that part_003 needs (it is one char short; the missing char is 'T' at 1167).
set -euo pipefail
ROOT=data_room/primary/ym_v174_final/input_v3
RES="$RUNNER_TEMP/v174-results"
WORK="$RUNNER_TEMP/v174-v3"
mkdir -p "$RES" "$WORK/repaired" "$WORK/extract"
python - <<'PY'
import json, hashlib, pathlib, base64, lzma, os
root=pathlib.Path('data_room/primary/ym_v174_final/input_v3')
res=pathlib.Path(os.environ['RUNNER_TEMP'])/'v174-results'
work=pathlib.Path(os.environ['RUNNER_TEMP'])/'v174-v3'
m=json.loads((root/'manifest.json').read_text())
alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
repaired=[]; audit=[]
for ent in m['parts']:
    s=(root/ent['name']).read_text().strip(); got=hashlib.sha256(s.encode()).hexdigest()
    if len(s)==ent['chars'] and got==ent['sha256']:
        rs=s; mode='exact'
    elif len(s)==ent['chars']-1:
        rs=None
        for pos in range(len(s)+1):
            for ch in alphabet:
                cand=s[:pos]+ch+s[pos:]
                if hashlib.sha256(cand.encode()).hexdigest()==ent['sha256']:
                    rs=cand; mode=f'insert:{pos}:{ch}'; break
            if rs is not None: break
        if rs is None: raise RuntimeError(f'unable to repair {ent["name"]}')
    else:
        raise RuntimeError(f'unexpected shard {ent["name"]}: len={len(s)} expected={ent["chars"]} sha={got}')
    repaired.append(rs); audit.append({'name':ent['name'],'input_chars':len(s),'output_chars':len(rs),'mode':mode,'sha256':hashlib.sha256(rs.encode()).hexdigest()})
b64=''.join(repaired)
assert len(b64)==m['base64_chars']
raw=base64.b64decode(b64,validate=True); sha=hashlib.sha256(raw).hexdigest()
assert sha==m['archive_sha256'] and len(raw)==m['archive_bytes']
lzma.decompress(raw)
(work/'input.tar.xz').write_bytes(raw)
(res/'v3_repair_audit.json').write_text(json.dumps({'schema':'GZYM_V174_V3_REPAIR_AUDIT','manifest':m,'repairs':audit,'archive_sha256':sha,'archive_bytes':len(raw)},indent=2))
(res/'v3_status.txt').write_text('COMPLETE\n')
PY
tar -tJf "$WORK/input.tar.xz" | sort > "$RES/v3_inventory.txt"
tar -xJf "$WORK/input.tar.xz" -C "$WORK/extract"
echo "input_v3 reassembled and extracted to $WORK/extract"
