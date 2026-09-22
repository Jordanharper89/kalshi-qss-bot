from pathlib import Path
import json,math
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
TOTAL_HURDLE=0.020

def _target(o,n):
    if n=="RETURN_POS": return float(o["future_return"])>0
    if n=="RETURN_NEG": return float(o["future_return"])<0
    if n=="UP_5C": return bool(o.get("hit_plus_05"))
    if n=="DOWN_5C": return bool(o.get("hit_minus_05"))
    if n=="UP_10C": return bool(o.get("hit_plus_10"))
    if n=="DOWN_10C": return bool(o.get("hit_minus_10"))
    raise RuntimeError("UNKNOWN_TARGET")

def status(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    freeze=json.loads((rt/"opd_gen2_candidate_freeze.json").read_text(encoding="utf-8"))
    states={}
    p=rt/"opd_gen2_post_freeze_state_ledger.jsonl"
    if p.exists():
        with p.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    x=json.loads(line);states[x["state_id"]]=x
    outcomes={}
    q=rt/"opd_033_prospective_outcome_ledger.jsonl"
    if q.exists():
        with q.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    x=json.loads(line);outcomes[x["state_id"]]=x

    rows=[]
    for c in freeze["candidates"]:
        fid=c["family_id"];h=int(c["horizon_seconds"]);target=c["target"]
        base=[(s,outcomes[sid]) for sid,s in states.items()
              if sid in outcomes and int(s["horizon_seconds"])==h]
        trig=[(s,o) for s,o in base if fid in (s.get("matched_family_ids") or [])]
        br=sum(_target(o,target) for _,o in base)/len(base) if base else None
        cr=sum(_target(o,target) for _,o in trig)/len(trig) if trig else None
        lift=cr-br if br is not None and cr is not None else None
        dret=[float(o["future_return"]) for _,o in trig]
        fav=[float(o["mfe"]) for _,o in trig]
        adv=[-float(o["mae"]) for _,o in trig]
        mean=sum(dret)/len(dret) if dret else None
        net=mean-TOTAL_HURDLE if mean is not None else None
        mf=sum(fav)/len(fav) if fav else None
        ma=sum(adv)/len(adv) if adv else None
        rr=mf/max(ma,1e-9) if mf is not None and ma is not None else None
        checks={
            "baseline_n":len(base)>=500,
            "trigger_n":len(trig)>=100,
            "tickers":len({s["ticker"] for s,_ in trig})>=10,
            "net_expected":net is not None and net>=0.005,
            "favorable_excursion":mf is not None and mf>=0.03,
            "reward_risk":rr is not None and rr>=1.20,
        }
        rows.append({"family_id":fid,"horizon_seconds":h,"target":target,
                     "gen2_states_total":sum(int(s["horizon_seconds"])==h for s in states.values()),
                     "resolved_baseline_n":len(base),"resolved_trigger_n":len(trig),
                     "trigger_tickers":len({s["ticker"] for s,_ in trig}),
                     "baseline_rate":br,"trigger_rate":cr,"lift":lift,
                     "directional_mean_return":mean,"net_expected_after_hurdle":net,
                     "mean_favorable_excursion":mf,"mean_adverse_excursion":ma,
                     "reward_risk_proxy":rr,"checks":checks,
                     "passed_checks":sum(checks.values()),
                     "edge_certified":False})

    out=rt/"opd_gen2_fresh_evidence_status.json"
    out.write_text(json.dumps(rows,indent=2,sort_keys=True),encoding="utf-8")
    print("="*96);print("ORACLE GEN2 FRESH EVIDENCE STATUS");print("="*96)
    print("GENERATION=",freeze["generation"],"ACTIVATION_EPOCH=",freeze["activation_epoch"])
    print("POST_FREEZE_STATES=",len(states),"POST_FREEZE_OUTCOMES=",sum(k in outcomes for k in states))
    for x in rows:
        print("-"*96)
        print("FAMILY_ID=",x["family_id"],"H=",x["horizon_seconds"],"TARGET=",x["target"])
        print("GEN2_STATES_TOTAL=",x["gen2_states_total"])
        print("RESOLVED_BASELINE_N=",x["resolved_baseline_n"])
        print("RESOLVED_TRIGGER_N=",x["resolved_trigger_n"])
        print("TRIGGER_TICKERS=",x["trigger_tickers"])
        print("LIFT=",x["lift"])
        print("NET_EXPECTED_AFTER_HURDLE=",x["net_expected_after_hurdle"])
        print("REWARD_RISK=",x["reward_risk_proxy"])
        print("PASSED_CHECKS=",str(x["passed_checks"])+"/6")
        print("FAILED_CHECKS=",",".join(k for k,v in x["checks"].items() if not v) or "NONE")
        print("EDGE_CERTIFIED=FALSE")
    print("="*96)
    print("SELECTION_REUSED=FALSE")
    print("PROBABILITY/DIRECTION/PUBLICATION/EXECUTION=FALSE/FALSE/FALSE/FALSE")
    return rows

if __name__=="__main__": status()
