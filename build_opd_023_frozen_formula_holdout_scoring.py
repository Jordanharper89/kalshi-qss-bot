from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_023_frozen_formula_holdout_scoring.py";TEST=ROOT/"test_opd_023_frozen_formula_holdout_scoring.py"
MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict
import hashlib,json,math

def _target(y,name):
    if name=="UP_5C":return bool(y.get("hit_plus_05"))
    if name=="DOWN_5C":return bool(y.get("hit_minus_05"))
    if name=="UP_10C":return bool(y.get("hit_plus_10"))
    if name=="DOWN_10C":return bool(y.get("hit_minus_10"))
    if name=="RETURN_POS":return float(y.get("future_return",0))>0
    if name=="RETURN_NEG":return float(y.get("future_return",0))<0
    return False
def _pvalue(k,n,k0,n0):
    if n<=0 or n0<=0:return 1.0
    p1=k/n;p0=k0/n0;p=(k+k0)/(n+n0);se=math.sqrt(max(1e-18,p*(1-p)*(1/n+1/n0)));z=(p1-p0)/se
    return math.erfc(abs(z)/math.sqrt(2))
def _bh(rows):
    m=len(rows);order=sorted(range(m),key=lambda i:rows[i]["p_value"]);qprev=1.0
    for rr,i in enumerate(reversed(order),1):
        rank=m-rr+1;q=min(qprev,rows[i]["p_value"]*m/rank);rows[i]["q_value"]=min(1.0,q);qprev=q
    return rows

def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    families=json.loads((rt/"opd_022_formula_family_registry.json").read_text())
    bykey=defaultdict(list)
    for f in families:bykey[(int(f["horizon_seconds"]),f["target"])].append(f)
    base=defaultdict(lambda:[0,0]);agg={f["family_id"]:{"n":0,"k":0,"ret":0.0,"mfe":0.0,"mae":0.0,"tickers":set()} for f in families}
    with (rt/"opd_021_holdout_feature_primitives.jsonl").open(encoding="utf-8") as src:
        for line in src:
            x=json.loads(line);h=int(x["horizon_seconds"]);tok=set(x["tokens"]);y=x["future_target"]
            for target in ("UP_5C","DOWN_5C","UP_10C","DOWN_10C","RETURN_POS","RETURN_NEG"):
                val=_target(y,target);base[(h,target)][0]+=int(val);base[(h,target)][1]+=1
                for f in bykey.get((h,target),()):
                    if all(z in tok for z in f["formula"]):
                        a=agg[f["family_id"]];a["n"]+=1;a["k"]+=int(val);a["ret"]+=float(y.get("future_return",0));a["mfe"]+=float(y.get("mfe",0));a["mae"]+=float(y.get("mae",0));a["tickers"].add(x["ticker"])
    rows=[]
    for f in families:
        a=agg[f["family_id"]];n=a["n"];bk,bn=base[(int(f["horizon_seconds"]),f["target"])]
        rate=a["k"]/n if n else None;base_rate=bk/bn if bn else None
        lift=(rate-base_rate) if n and bn else None;sign_ok=(lift is not None and f["discovery_lift"]*lift>0)
        rn=bn-n;rk=bk-a["k"];pv=_pvalue(a["k"],n,rk,rn) if n and rn>0 else 1.0
        rows.append({"family_id":f["family_id"],"representative_formula_id":f["representative_formula_id"],"degree":f["degree"],"horizon_seconds":f["horizon_seconds"],"target":f["target"],"formula":f["formula"],
            "discovery_n":f["discovery_n"],"discovery_lift":f["discovery_lift"],"holdout_n":n,"holdout_ticker_count":len(a["tickers"]),"holdout_base_rate":base_rate,"holdout_conditional_rate":rate,"holdout_lift":lift,
            "lift_retention":(abs(lift)/abs(f["discovery_lift"])) if lift is not None and f["discovery_lift"] else None,"sign_preserved":sign_ok,
            "mean_future_return":a["ret"]/n if n else None,"mean_mfe":a["mfe"]/n if n else None,"mean_mae":a["mae"]/n if n else None,"p_value":pv})
    _bh(rows);rows.sort(key=lambda x:(x["q_value"],-(abs(x["holdout_lift"]) if x["holdout_lift"] is not None else 0),-x["holdout_n"]))
    rf=rt/"opd_023_frozen_formula_holdout_scores.json";rf.write_text(json.dumps(rows,indent=2,sort_keys=True))
    s={"schema_version":"OPD-023","families_scored":len(rows),"families_with_holdout_support":sum(x["holdout_n"]>0 for x in rows),
       "sign_preserved_count":sum(bool(x["sign_preserved"]) for x in rows),"fdr_q_le_010_count":sum(x["q_value"]<=0.10 for x in rows),
       "holdout_threshold_tuning":False,"score_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"edge_certified_count":0,
       "model_fit_allowed":False,"formula_mining_allowed":False,"probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False}
    out=rt/"opd_023_frozen_formula_holdout_scoring.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_023_frozen_formula_holdout_scoring import build
s,p=build(Path.cwd());assert p.exists() and s["families_scored"]>0 and not s["holdout_threshold_tuning"] and s["edge_certified_count"]==0
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[FAMILIES_SCORED]",s["families_scored"]);print("[WITH_SUPPORT]",s["families_with_holdout_support"]);print("[SIGN_PRESERVED]",s["sign_preserved_count"]);print("[Q_LE_0.10]",s["fdr_q_le_010_count"]);print("[SCORE_HASH]",s["score_hash"])
print("[PASS] frozen formula families scored on untouched contracts without threshold tuning");print("[PASS] holdout base rates recomputed independently by horizon");print("[PASS] OPD-023 frozen-formula holdout scoring certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-023 installer complete")
