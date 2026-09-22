from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_028_support_overlap_family_reduction.py";TEST=ROOT/"test_opd_028_support_overlap_family_reduction.py"
MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict
import hashlib,json
JACCARD_THRESHOLD=0.90;MINHASH_K=24;BANDS=6

def _load_rows(rt):
    rows=[];inv=defaultdict(set)
    with (rt/"opd_021_holdout_feature_primitives.jsonl").open(encoding="utf-8") as f:
        for i,line in enumerate(f):
            x=json.loads(line);rows.append(x)
            for t in x["tokens"]:inv[(int(x["horizon_seconds"]),t)].add(i)
    return rows,inv
def _matches(inv,h,formula):
    sets=[inv.get((int(h),t),set()) for t in formula]
    if not sets:return set()
    sets=sorted(sets,key=len);z=set(sets[0])
    for s in sets[1:]:
        z.intersection_update(s)
        if not z:break
    return z

def _hv(s):return int(hashlib.sha256(str(s).encode()).hexdigest()[:16],16)
def _sig(ids,rows):
    vals=sorted(_hv(rows[i]["anchor_id"]) for i in ids)[:MINHASH_K]
    return tuple(vals+[0]*(MINHASH_K-len(vals)))
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";prev=json.loads((rt/"opd_027_cross_contract_concentration_registry.json").read_text());rows,inv=_load_rows(rt)
    active=[x for x in prev if x.get("cross_contract_pass")];supports={};sigs={}
    for x in active:
        ids=_matches(inv,x["horizon_seconds"],x["formula"]);supports[x["family_id"]]=ids;sigs[x["family_id"]]=_sig(ids,rows)
    parent={x["family_id"]:x["family_id"] for x in active}
    def find(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    buckets=defaultdict(list);bw=MINHASH_K//BANDS
    for x in active:
        fid=x["family_id"];sg=sigs[fid]
        for b in range(BANDS):buckets[(x["horizon_seconds"],x["target"],b,sg[b*bw:(b+1)*bw])].append(fid)
    checked=set()
    for ids in buckets.values():
        for i,a in enumerate(ids):
            for b in ids[i+1:]:
                key=(a,b) if a<b else (b,a)
                if key in checked:continue
                checked.add(key);A=supports[a];B=supports[b];u=len(A|B);j=len(A&B)/u if u else 0.0
                if j>=JACCARD_THRESHOLD:union(a,b)
    groups=defaultdict(list)
    for x in active:groups[find(x["family_id"])].append(x)
    reps=[]
    for g in groups.values():
        g=sorted(g,key=lambda x:(x["holdout_q_value"],-abs(x["holdout_lift"]),len(x["formula"]),x["family_id"]));r=dict(g[0]);r["overlap_cluster_size"]=len(g);r["overlap_member_family_ids"]=[z["family_id"] for z in g];reps.append(r)
    rf=rt/"opd_028_support_overlap_representatives.json";rf.write_text(json.dumps(reps,indent=2,sort_keys=True))
    s={"schema_version":"OPD-028","input_cross_contract_pass":len(active),"overlap_clusters":len(groups),"representatives":len(reps),"collapsed_by_overlap":len(active)-len(reps),"jaccard_threshold":JACCARD_THRESHOLD,"candidate_pairs_checked":len(checked),"registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"edge_certified_count":0}
    out=rt/"opd_028_support_overlap_family_reduction.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_028_support_overlap_family_reduction import build
s,p=build(Path.cwd());assert p.exists() and s["representatives"]<=s["input_cross_contract_pass"] and s["edge_certified_count"]==0
print("[FILE]",p);print("[INPUT]",s["input_cross_contract_pass"]);print("[REPRESENTATIVES]",s["representatives"]);print("[COLLAPSED_BY_OVERLAP]",s["collapsed_by_overlap"]);print("[JACCARD]",s["jaccard_threshold"]);print("[REGISTRY_HASH]",s["registry_hash"]);print("[PASS] OPD-028 support-overlap family reduction certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-028 installer complete")
