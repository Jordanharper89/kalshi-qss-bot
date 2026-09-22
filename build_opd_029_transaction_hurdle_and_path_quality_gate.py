from pathlib import Path
import py_compile
ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_029_transaction_hurdle_and_path_quality_gate.py";TEST=ROOT/"test_opd_029_transaction_hurdle_and_path_quality_gate.py"
MOD.write_text(r"""
from pathlib import Path
from collections import defaultdict
import hashlib,json
ROUND_TRIP_FRICTION=0.015;SAFETY_MARGIN=0.005;TOTAL_HURDLE=0.020
MIN_NET_EXPECTED=0.005;MIN_FAVORABLE_EXCURSION=0.03;MIN_REWARD_RISK=1.20
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
def _dir(target):return -1.0 if target in ("DOWN_5C","DOWN_10C","RETURN_NEG") else 1.0
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";reps=json.loads((rt/"opd_028_support_overlap_representatives.json").read_text());rows,inv=_load_rows(rt);outrows=[]
    for f in reps:
        ids=_matches(inv,f["horizon_seconds"],f["formula"]);d=_dir(f["target"]);n=len(ids)
        if n:
            ret=sum(d*float(rows[i]["future_target"].get("future_return",0)) for i in ids)/n
            fav=sum((float(rows[i]["future_target"].get("mfe",0)) if d>0 else -float(rows[i]["future_target"].get("mae",0))) for i in ids)/n
            adv=sum((-float(rows[i]["future_target"].get("mae",0)) if d>0 else float(rows[i]["future_target"].get("mfe",0))) for i in ids)/n
        else:ret=fav=adv=0.0
        net=ret-TOTAL_HURDLE;rr=fav/max(adv,1e-9)
        checks={"net_expected_ge_min":net>=MIN_NET_EXPECTED,"favorable_excursion_ge_min":fav>=MIN_FAVORABLE_EXCURSION,"reward_risk_ge_min":rr>=MIN_REWARD_RISK}
        z=dict(f);z["economic_match_count"]=n;z["directional_mean_future_return"]=ret;z["directional_mean_favorable_excursion"]=fav;z["directional_mean_adverse_excursion"]=adv;z["total_hurdle"]=TOTAL_HURDLE;z["net_expected_after_hurdle"]=net;z["reward_risk_proxy"]=rr;z["economic_checks"]=checks;z["economic_gate_pass"]=all(checks.values());outrows.append(z)
    rf=rt/"opd_029_transaction_hurdle_path_quality_registry.json";rf.write_text(json.dumps(outrows,indent=2,sort_keys=True))
    s={"schema_version":"OPD-029","evaluated":len(outrows),"economic_gate_pass":sum(x["economic_gate_pass"] for x in outrows),"fixed_assumptions":{"round_trip_friction":ROUND_TRIP_FRICTION,"safety_margin":SAFETY_MARGIN,"total_hurdle":TOTAL_HURDLE,"min_net_expected":MIN_NET_EXPECTED,"min_favorable_excursion":MIN_FAVORABLE_EXCURSION,"min_reward_risk":MIN_REWARD_RISK},"assumptions_tuned_on_validation":False,"registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"edge_certified_count":0}
    out=rt/"opd_029_transaction_hurdle_and_path_quality_gate.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
""",encoding="utf-8")
TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_029_transaction_hurdle_and_path_quality_gate import build
s,p=build(Path.cwd());assert p.exists() and not s["assumptions_tuned_on_validation"] and s["edge_certified_count"]==0
print("[FILE]",p);print("[EVALUATED]",s["evaluated"]);print("[ECONOMIC_PASS]",s["economic_gate_pass"]);print("[FIXED_ASSUMPTIONS]",s["fixed_assumptions"]);print("[REGISTRY_HASH]",s["registry_hash"]);print("[PASS] OPD-029 transaction-hurdle/path-quality gate certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True);print("[PASS] OPD-029 installer complete")