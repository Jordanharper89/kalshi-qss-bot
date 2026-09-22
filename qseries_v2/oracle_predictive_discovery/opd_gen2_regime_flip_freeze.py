from pathlib import Path
import json,time,hashlib
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

def _canon(x): return json.dumps(x,sort_keys=True,separators=(",",":"))

def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    audit=json.loads((rt/"opd_gen2_prospective_shortlist_audit.json").read_text(encoding="utf-8"))
    outcomes=[]
    p=rt/"opd_033_prospective_outcome_ledger.jsonl"
    if p.exists():
        with p.open(encoding="utf-8") as f:
            outcomes=[json.loads(x) for x in f if x.strip()]
    cutoff=max((float(x["resolution_epoch"]) for x in outcomes),default=0.0)
    cands=[x for x in audit if x.get("trigger_n",0)>=20 and x.get("trigger_tickers",0)>=4
           and x.get("prospective_lift") is not None and x["prospective_lift"]>0
           and x.get("net_expected_after_hurdle") is not None and x["net_expected_after_hurdle"]>0
           and x.get("reward_risk_proxy") is not None and x["reward_risk_proxy"]>1.0]
    frozen=[]
    for x in cands:
        y={k:x[k] for k in ("family_id","horizon_seconds","target","formula","historical_holdout_lift",
                              "baseline_n","trigger_n","trigger_tickers","prospective_lift",
                              "directional_mean_return","net_expected_after_hurdle",
                              "mean_favorable_excursion","mean_adverse_excursion","reward_risk_proxy")}
        y["selection_basis"]="GEN1_PROSPECTIVE_REGIME_FLIP_SELECTION_ONLY"
        y["historical_sign_preserved"]=bool(x.get("sign_preserved"))
        y["edge_certified"]=False
        frozen.append(y)
    body={"schema_version":"OPD-GEN2-FREEZE-1","generation":2,"activation_epoch":time.time(),
          "selection_cutoff_resolution_epoch":cutoff,"selection_rows":len(outcomes),
          "candidate_count":len(frozen),"candidates":frozen,
          "selection_only":True,"edge_certified":False,"execution_authority":False,
          "probability_enabled":False,"direction_enabled":False,"publication_allowed":False}
    body["freeze_id"]=hashlib.sha256(_canon({k:v for k,v in body.items() if k!="activation_epoch"}).encode()).hexdigest()
    dst=rt/"opd_gen2_candidate_freeze.json"
    if dst.exists():
        old=json.loads(dst.read_text(encoding="utf-8"))
        old_cmp={k:v for k,v in old.items() if k!="activation_epoch"}
        new_cmp={k:v for k,v in body.items() if k!="activation_epoch"}
        if old_cmp!=new_cmp: raise RuntimeError("GEN2_FROZEN_CANDIDATE_DRIFT")
        body=old
    else:
        dst.write_text(json.dumps(body,indent=2,sort_keys=True),encoding="utf-8")
    print("="*92);print("ORACLE GEN2 REGIME-FLIP FREEZE");print("="*92)
    print("GENERATION=2");print("SELECTION_ROWS=",body["selection_rows"])
    print("CANDIDATE_COUNT=",body["candidate_count"])
    print("ACTIVATION_EPOCH=",body["activation_epoch"])
    print("SELECTION_CUTOFF_RESOLUTION_EPOCH=",body["selection_cutoff_resolution_epoch"])
    for x in body["candidates"]:
        print("FAMILY_ID=",x["family_id"],"H=",x["horizon_seconds"],"TARGET=",x["target"])
        print("LIVE_SELECTION_LIFT=",x["prospective_lift"],"NET_AFTER_HURDLE=",x["net_expected_after_hurdle"])
        print("TRIGGER_N=",x["trigger_n"],"TICKERS=",x["trigger_tickers"],"EDGE_CERTIFIED=FALSE")
    print("PROBABILITY/DIRECTION/PUBLICATION/EXECUTION=FALSE/FALSE/FALSE/FALSE")
    return body,dst

if __name__=="__main__": build()
