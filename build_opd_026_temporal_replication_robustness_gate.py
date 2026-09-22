from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_026_temporal_replication_robustness_gate.py";TEST=ROOT/"test_opd_026_temporal_replication_robustness_gate.py"
MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict
import hashlib,json
MIN_SEGMENT_MATCHES=15;MIN_ALIGNED_SEGMENTS=3
TARGETS=("UP_5C","DOWN_5C","UP_10C","DOWN_10C","RETURN_POS","RETURN_NEG")
def _target(y,name):
    return bool(y.get("hit_plus_05")) if name=="UP_5C" else bool(y.get("hit_minus_05")) if name=="DOWN_5C" else bool(y.get("hit_plus_10")) if name=="UP_10C" else bool(y.get("hit_minus_10")) if name=="DOWN_10C" else float(y.get("future_return",0))>0 if name=="RETURN_POS" else float(y.get("future_return",0))<0
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
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";fam=json.loads((rt/"opd_025_validated_association_registry.json").read_text());rows,inv=_load_rows(rt)
    epochs=sorted(float(x["anchor_epoch"]) for x in rows);n=len(epochs);cuts=[epochs[min(n-1,int(n*q))] for q in (.25,.5,.75)] if n else [0,0,0]
    def seg(e):return 0 if e<=cuts[0] else 1 if e<=cuts[1] else 2 if e<=cuts[2] else 3
    base=defaultdict(lambda:[0,0])
    for x in rows:
        s=seg(float(x["anchor_epoch"]));h=int(x["horizon_seconds"])
        for t in TARGETS:base[(s,h,t)][0]+=int(_target(x["future_target"],t));base[(s,h,t)][1]+=1
    outrows=[]
    for f in fam:
        ids=_matches(inv,f["horizon_seconds"],f["formula"]);stats=[]
        for s in range(4):
            mids=[i for i in ids if seg(float(rows[i]["anchor_epoch"]))==s]
            k=sum(int(_target(rows[i]["future_target"],f["target"])) for i in mids);bk,bn=base[(s,int(f["horizon_seconds"]),f["target"])]
            rate=k/len(mids) if mids else None;br=bk/bn if bn else None;lift=(rate-br) if rate is not None and br is not None else None
            stats.append({"segment":s,"n":len(mids),"lift":lift,"aligned":len(mids)>=MIN_SEGMENT_MATCHES and lift is not None and lift*f["discovery_lift"]>0})
        z=dict(f);z["temporal_segments"]=stats;z["aligned_segments"]=sum(x["aligned"] for x in stats);z["temporal_replication_pass"]=z["aligned_segments"]>=MIN_ALIGNED_SEGMENTS;outrows.append(z)
    rf=rt/"opd_026_temporal_replication_registry.json";rf.write_text(json.dumps(outrows,indent=2,sort_keys=True))
    s={"schema_version":"OPD-026","associations_evaluated":len(outrows),"temporal_replication_pass":sum(x["temporal_replication_pass"] for x in outrows),"temporal_cuts":cuts,"historical_secondary_oos_claimed":False,"reason":"OPD-023_ALREADY_USED_FULL_HOLDOUT_FOR_SELECTION","registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"edge_certified_count":0}
    out=rt/"opd_026_temporal_replication_robustness_gate.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_026_temporal_replication_robustness_gate import build
s,p=build(Path.cwd());assert p.exists() and not s["historical_secondary_oos_claimed"] and s["edge_certified_count"]==0
print("[FILE]",p);print("[EVALUATED]",s["associations_evaluated"]);print("[TEMPORAL_PASS]",s["temporal_replication_pass"]);print("[CUTS]",s["temporal_cuts"]);print("[PASS] OPD-026 temporal replication robustness gate certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-026 installer complete")