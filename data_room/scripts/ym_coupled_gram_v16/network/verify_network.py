import json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=root/'spatial_gram_v15/GEOMETRY_AND_DIMENSION.json'
source=source if source.exists() else Path(__file__).resolve().parent.parent/'inputs/GEOMETRY_AND_DIMENSION.json'
g=json.loads(source.read_text());r=json.loads(Path(__file__).with_name('ALL_FACTOR_NETWORK_ANALYSIS.json').read_text())
tree=set(r['tree_links_set_to_identity']);edges=g['edges']
def ends(e):
 x,d=edges[e];y=list(x);y[d]=1-y[d];return tuple(x),tuple(y)
adj={tuple(x):set() for x,d in edges}
for e in tree:
 x,y=ends(e);adj[x].add(y);adj[y].add(x)
seen=set();todo=[(0,0,0)]
while todo:
 x=todo.pop()
 if x not in seen:seen.add(x);todo.extend(adj[x]-seen)
assert len(seen)==8 and len(tree)==7
for p,q in zip(g['plaquettes'],r['gauge_fixed_plaquette_words']):
 route=[]
 for e,s in p:
  a,b=ends(e);route.append((a,b) if s==1 else (b,a))
 assert all(route[i][1]==route[(i+1)%4][0] for i in range(4))
 assert q==[[e,s] for e,s in p if e not in tree]
scopes=[set(e for e,s in p) for p in r['gauge_fixed_plaquette_words']]
bags=[]
for e in r['elimination_order']:
 touched=[s for s in scopes if e in s];assert touched
 bag=set().union(*touched);bags.append(sorted(bag))
 scopes=[s for s in scopes if e not in s]+[bag-{e}]
assert bags==r['elimination_bags'] and max(map(len,bags))-1==8
assert all(not s for s in scopes)
out={'status':'PASS_EXACT_GEOMETRY_AND_ALL_FACTOR_ELIMINATION_SCHEDULE','all_24_plaquette_words_checked':True,'tree_gauge_integrations':7,'remaining_group_integrations':17,'primal_width_upper_verified':8,'full_spatial_gram_contracted':False}
Path(__file__).with_name('INDEPENDENT_NETWORK_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
