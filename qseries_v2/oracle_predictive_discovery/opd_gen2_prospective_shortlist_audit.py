from pathlib import Path
import json,math
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
TOTAL_HURDLE=0.020

def _target(o,n):
    if n=="UP_5C":return bool(o["hit_plus_05"])
    if n=="DOWN_5C":return bool(o["hit_minus_05"])
    if n=="UP_10C":return bool(o["hit_plus_10"])
    if n=="DOWN_10C":return bool(o["hit_minus_10"])
    if n=="RETURN_POS":return float(o["future_return"])>0
    return float(o["future_return"])<0

def _dir(n):return -1.0 if n in ("DOWN_5C","DOWN_10C","RETURN_NEG") else 1.0
def _match(s,f):return all(t in set(s.get("tokens") or []) for t in f)

def audit(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    fam=json.loads((rt/"opd_028_support_overlap_representatives.json").read_text(encoding="utf-8"))
    states={}
    with (rt/"opd_032_prospective_state_ledger.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                x=json.loads(line);states[x["state_id"]]=x
    outcomes={}
    with (rt/"opd_033_prospective_outcome_ledger.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                x=json.loads(line);outcomes[x["state_id"]]=x
    resolved=[(states[k],o) for k,o in outcomes.items() if k in states]
    rows=[]
    for c in fam:
        h=int(c["horizon_seconds"]);target=c["target"];d=_dir(target)
        base=[(s,o) for s,o in resolved if int(s["horizon_seconds"])==h]
        tr=[(s,o) for s,o in base if _match(s,c["formula"])]
        br=sum(_target(o,target) for _,o in base)/len(base) if base else None
        cr=sum(_target(o,target) for _,o in tr)/len(tr) if tr else None
        lift=cr-br if br is not None and cr is not None else None
        rr=[d*float(o["future_return"]) for _,o in tr]
        fav=[float(o["mfe"]) if d>0 else -float(o["mae"]) for _,o in tr]
        adv=[-float(o["mae"]) if d>0 else float(o["mfe"]) for _,o in tr]
        mean=sum(rr)/len(rr) if rr else None
        mf=sum(fav)/len(fav) if fav else None;ma=sum(adv)/len(adv) if adv else None
        net=mean-TOTAL_HURDLE if mean is not None else None
        rrp=mf/max(ma,1e-9) if mf is not None and ma is not None else None
        hist=float(c.get("holdout_lift") or c.get("discovery_lift") or 0)
        sign=lift is not None and hist*lift>0
        rows.append({"family_id":c["family_id"],"horizon_seconds":h,"target":target,"formula":c["formula"],
          "historical_holdout_lift":hist,"baseline_n":len(base),"trigger_n":len(tr),
          "trigger_tickers":len({s["ticker"] for s,_ in tr}),"prospective_lift":lift,
          "sign_preserved":sign,"directional_mean_return":mean,"net_expected_after_hurdle":net,
          "mean_favorable_excursion":mf,"mean_adverse_excursion":ma,"reward_risk_proxy":rrp,
          "gen2_shortlist":len(tr)>=10 and len({s["ticker"] for s,_ in tr})>=3 and sign and
                           net is not None and net>0 and mf is not None and mf>0 and rrp is not None and rrp>1.0})
    rows.sort(key=lambda x:(not x["gen2_shortlist"],-(x["net_expected_after_hurdle"] if x["net_expected_after_hurdle"] is not None else -999),
                            -x["trigger_n"],x["family_id"]))
    p=rt/"opd_gen2_prospective_shortlist_audit.json";p.write_text(json.dumps(rows,indent=2,sort_keys=True))
    print("="*96);print("ORACLE GEN2 PROSPECTIVE SHORTLIST AUDIT");print("="*96)
    print("RESOLVED_SELECTION_ROWS=",len(resolved));print("ROBUST_FAMILIES_AUDITED=",len(rows))
    print("GEN2_SHORTLIST_COUNT=",sum(x["gen2_shortlist"] for x in rows))
    for i,x in enumerate(rows,1):
        print("-"*96);print("RANK=",i,"FAMILY_ID=",x["family_id"],"H=",x["horizon_seconds"],"TARGET=",x["target"])
        print("BASELINE_N=",x["baseline_n"],"TRIGGER_N=",x["trigger_n"],"TICKERS=",x["trigger_tickers"])
        print("LIFT=",x["prospective_lift"],"SIGN_PRESERVED=",x["sign_preserved"])
        print("NET_EXPECTED_AFTER_HURDLE=",x["net_expected_after_hurdle"],"REWARD_RISK=",x["reward_risk_proxy"])
        print("GEN2_SHORTLIST=",x["gen2_shortlist"])
    print("="*96);print("SELECTION_ONLY=TRUE");print("EDGE_CERTIFIED=FALSE")
    print("PROBABILITY/DIRECTION/PUBLICATION/EXECUTION=FALSE/FALSE/FALSE/FALSE")
    return rows

if __name__=="__main__":audit()
