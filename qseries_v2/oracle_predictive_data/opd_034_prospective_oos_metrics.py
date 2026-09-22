
from pathlib import Path
import hashlib,json,math
def _target(y,n):
    return bool(y["hit_plus_05"]) if n=="UP_5C" else bool(y["hit_minus_05"]) if n=="DOWN_5C" else bool(y["hit_plus_10"]) if n=="UP_10C" else bool(y["hit_minus_10"]) if n=="DOWN_10C" else float(y["future_return"])>0 if n=="RETURN_POS" else float(y["future_return"])<0
def _dir(n):return -1.0 if n in ("DOWN_5C","DOWN_10C","RETURN_NEG") else 1.0
def _p(k,n,k0,n0):
    if min(n,n0)<=0:return 1.0
    p1=k/n;p0=k0/n0;p=(k+k0)/(n+n0);se=math.sqrt(max(1e-18,p*(1-p)*(1/n+1/n0)));return math.erfc(abs((p1-p0)/se)/math.sqrt(2))
def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data";freeze=json.loads((rt/"opd_031_prospective_candidate_freeze.json").read_text())
    states={};sp=rt/"opd_032_prospective_state_ledger.jsonl";op=rt/"opd_033_prospective_outcome_ledger.jsonl"
    if sp.exists():
        with sp.open(encoding="utf-8") as f:
            for line in f:
                x=json.loads(line);states[x["state_id"]]=x
    outcomes={}
    if op.exists():
        with op.open(encoding="utf-8") as f:
            for line in f:
                x=json.loads(line);outcomes[x["state_id"]]=x
    resolved=[(states[k],v) for k,v in outcomes.items() if k in states];rows=[]
    for c in freeze["candidates"]:
        h=int(c["horizon_seconds"]);target=c["target"];d=_dir(target)
        base=[(s,o) for s,o in resolved if int(s["horizon_seconds"])==h];tr=[(s,o) for s,o in base if c["family_id"] in s["matched_family_ids"]]
        bk=sum(int(_target(o,target)) for _,o in base);k=sum(int(_target(o,target)) for _,o in tr)
        br=bk/len(base) if base else None;cr=k/len(tr) if tr else None;lift=(cr-br) if cr is not None and br is not None else None
        rr=[d*float(o["future_return"]) for _,o in tr];fav=[float(o["mfe"]) if d>0 else -float(o["mae"]) for _,o in tr];adv=[-float(o["mae"]) if d>0 else float(o["mfe"]) for _,o in tr]
        rows.append({"family_id":c["family_id"],"horizon_seconds":h,"target":target,"historical_holdout_lift":c["historical_holdout_lift"],
                     "baseline_n":len(base),"trigger_n":len(tr),"trigger_tickers":len({s["ticker"] for s,_ in tr}),"prospective_base_rate":br,
                     "prospective_conditional_rate":cr,"prospective_lift":lift,"lift_retention":abs(lift)/abs(c["historical_holdout_lift"]) if lift is not None and c["historical_holdout_lift"] else None,
                     "sign_preserved":lift is not None and lift*c["historical_holdout_lift"]>0,"p_value":_p(k,len(tr),bk-k,len(base)-len(tr)) if len(base)>len(tr) else 1.0,
                     "directional_mean_return":sum(rr)/len(rr) if rr else None,"mean_favorable_excursion":sum(fav)/len(fav) if fav else None,"mean_adverse_excursion":sum(adv)/len(adv) if adv else None})
    m=len(rows)
    for x in rows:x["q_value"]=min(1.0,x["p_value"]*m)
    rf=rt/"opd_034_prospective_oos_metrics_registry.json";rf.write_text(json.dumps(rows,indent=2,sort_keys=True))
    s={"schema_version":"OPD-034","resolved_states":len(resolved),"candidates_evaluated":len(rows),"registry_hash":hashlib.sha256(rf.read_bytes()).hexdigest(),"edge_certified_count":0,"execution_authority":False}
    out=rt/"opd_034_prospective_oos_metrics.json";out.write_text(json.dumps(s,indent=2,sort_keys=True));return s,out
