"""Reproducible all-factor gauge-fixed interaction graph analysis; no Haar contractions claimed."""
import json,random,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'spatial_gram_v15/GEOMETRY_AND_DIMENSION.json'
source=source if source.exists() else Path(__file__).resolve().parent.parent/'inputs/GEOMETRY_AND_DIMENSION.json'
g=json.loads(source.read_text());edges=g['edges'];plaquettes=g['plaquettes']
def endpoint(e):
    x,mu=edges[e];y=x.copy();y[mu]=(y[mu]+1)%2
    return tuple(x),tuple(y)
def tree(rng):
    par={tuple(x):tuple(x) for x,mu in edges}
    def root(x):
        while x!=par[x]:x=par[x]
        return x
    order=list(range(24));rng.shuffle(order);out=[]
    for e in order:
        x,y=map(root,endpoint(e))
        if x!=y:par[x]=y;out.append(e)
    assert len(out)==7
    return sorted(out)
def adjacency(scopes):
    a={x:set() for s in scopes for x in s}
    for s in scopes:
        for x in s:a[x].update(set(s)-{x})
    return a
def elimination(a,rng):
    a={k:set(v) for k,v in a.items()};order=[];bags=[]
    while a:
        def score(x):
            n=a[x];missing=sum(y not in a[z] for z in n for y in n if y!=z)//2
            return missing,len(n)
        best=min(map(score,a));c=[x for x in a if score(x)==best];x=rng.choice(c)
        n=a[x];bags.append(sorted({x}|n));order.append(x)
        for y in n:a[y].update(n-{y});a[y].discard(x)
        del a[x]
    return order,bags,max(map(len,bags))-1
def minor_lower(a):
    a={k:set(v) for k,v in a.items()};lb=0
    while a:
        v=min(a,key=lambda x:(len(a[x]),x));lb=max(lb,len(a[v]))
        if not a[v]:del a[v];continue
        u=min(a[v],key=lambda x:(len(a[x]),x));nbr=(a[u]|a[v])-{u,v}
        for x in nbr:a[x].discard(v);a[x].add(u)
        a[u]=nbr;del a[v]
    return lb
rng=random.Random(20260917);full=adjacency([{e for e,s in p} for p in plaquettes]);fullresults=[elimination(full,rng) for _ in range(64)]
best=None
for k in range(2048):
    t=tree(rng);scopes=[{e for e,s in p if e not in t} for p in plaquettes]
    a=adjacency(scopes);order,bags,width=elimination(a,rng)
    key=(width,sum(10**len(b) for b in bags),tuple(t))
    if best is None or key<best[0]:best=(key,t,scopes,order,bags,a)
_,t,scopes,order,bags,a=best
# Closed loops are gauge invariant; selected V15 basis insertions already have scopes among plaquettes.
assert set().union(*scopes)==set(range(24))-set(t)
assert len(scopes)==24 and all(scopes)
degrees={e:sum(e in s for s in scopes) for e in a}
# Exact sum dim(p,q)^2 provides a scale for complete local Fourier polynomial space.
def dim(p,q):return (p+1)*(q+1)*(p+q+2)//2
local_degree=4*466+2*292
fourier_dimension=sum(dim(p,q)**2 for p in range(local_degree+1) for q in range(local_degree+1-p))
record={
 'schema':'GZYM_V16_ALL_FACTOR_NETWORK_ANALYSIS','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'geometry':{'vertices':8,'links':24,'plaquettes':24},'random_seed':20260917,'spanning_trees_sampled':2048,
 'all_24_factors_retained':True,'tree_links_set_to_identity':t,'unfixed_links':sorted(a),
 'gauge_fixed_plaquette_words':[[[e,s] for e,s in p if e not in t] for p in plaquettes],
 'gauge_fixed_factor_scopes':[sorted(s) for s in scopes],
 'gauge_fixed_primal_induced_width_upper':max(map(len,bags))-1,
 'gauge_fixed_primal_treewidth_minor_lower':minor_lower(a),
 'elimination_order':order,'elimination_bags':bags,
 'ungauged_primal_induced_width_upper':min(x[2] for x in fullresults),'ungauged_treewidth_minor_lower':minor_lower(full),
 'factors_per_unfixed_link':degrees,
 'full_gram_conservative_per_link_polynomial_degree':local_degree,
 'unconstrained_local_fourier_basis_dimension_at_degree_bound':str(fourier_dimension),
 'warning':'Graph widths bound variable-elimination separator sizes only. They are neither evaluated Haar tensors nor exact tensor ranks. Local Fourier dimension is a complete ambient polynomial-space count, not a lower bound on optimally compressed ranks.',
 'full_spatial_gram_contracted':False,
}
Path(__file__).with_name('ALL_FACTOR_NETWORK_ANALYSIS.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ['gauge_fixed_primal_induced_width_upper','gauge_fixed_primal_treewidth_minor_lower','ungauged_primal_induced_width_upper','ungauged_treewidth_minor_lower','tree_links_set_to_identity','unconstrained_local_fourier_basis_dimension_at_degree_bound']},indent=2))
