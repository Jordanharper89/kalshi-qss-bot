from pathlib import Path
import json,time

execution_authority=False
publication_allowed=False

def _rows(p):
    if not p.exists(): return []
    out=[]
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try: out.append(json.loads(line))
                except Exception: pass
    return out

def run(root=None):
    root=Path(root or Path.cwd()).resolve()
    rt=root/"runtime"/"predictive_data"
    freeze=json.loads((rt/"opd_gen2_candidate_freeze.json").read_text(encoding="utf-8"))
    cands=list(freeze.get("candidates") or [])
    if not cands: raise RuntimeError("NO_GEN2_CANDIDATE")
    states=_rows(rt/"opd_032_prospective_state_ledger.jsonl")
    outcomes={x.get("state_id"):x for x in _rows(rt/"opd_033_prospective_outcome_ledger.jsonl")}
    best=None
    for c in cands:
        h=int(c["horizon_seconds"])
        eligible=[s for s in states if int(s.get("horizon_seconds",-1))==h and float(s.get("observed_epoch",0))>float(freeze["activation_epoch"])]
        if not eligible: continue
        s=max(eligible,key=lambda x:float(x.get("observed_epoch",0)))
        toks=set(s.get("tokens") or [])
        match=all(x in toks for x in c.get("formula") or [])
        resolved=[]
        for x in eligible:
            xt=set(x.get("tokens") or [])
            if all(q in xt for q in c.get("formula") or []) and x.get("state_id") in outcomes:
                resolved.append(outcomes[x["state_id"]])
        rets=[float(x.get("future_return",0.0)) for x in resolved]
        fresh_mean=(sum(rets)/len(rets)) if rets else None
        frozen_net=c.get("net_expected_after_hurdle")
        target=c.get("target")
        direction="UP" if target in ("RETURN_POS","UP_5C","UP_10C") else "DOWN"
        score={
            "candidate":c,"state":s,"match":match,"direction":direction,
            "fresh_resolved_trigger_n":len(resolved),
            "fresh_mean_return":fresh_mean,
            "frozen_selection_net_edge":frozen_net,
        }
        if best is None or float(s.get("observed_epoch",0))>float(best["state"].get("observed_epoch",0)):
            best=score
    print("="*104);print("ORACLE LIVE PREDICTION CANDIDATE NOW");print("="*104)
    if best is None:
        print("LIVE_PREDICTION=ABSTAIN");print("REASON=NO_POST_FREEZE_300S_STATE");print("EXECUTION_AUTHORITY=FALSE");return None
    c=best["candidate"];s=best["state"]
    print("TICKER=",s.get("ticker"));print("STATE_ID=",s.get("state_id"))
    print("HORIZON_SECONDS=",c.get("horizon_seconds"));print("FAMILY_ID=",c.get("family_id"))
    print("FORMULA_MATCH=",str(best["match"]).upper())
    print("FRESH_RESOLVED_TRIGGER_N=",best["fresh_resolved_trigger_n"])
    print("FRESH_MEAN_RETURN=",best["fresh_mean_return"])
    print("FROZEN_SELECTION_NET_EDGE_AFTER_2PCT=",best["frozen_selection_net_edge"])
    if best["match"] and best["frozen_selection_net_edge"] is not None and float(best["frozen_selection_net_edge"])>0:
        print("LIVE_PREDICTION_CANDIDATE=",best["direction"])
        print("EXPECTED_NET_EDGE_SELECTION_BASIS=",best["frozen_selection_net_edge"])
        print("PROFITABILITY_STATUS=","FRESH_SUPPORTED" if best["fresh_resolved_trigger_n"]>0 and (best["fresh_mean_return"] or 0)>0.02 else "UNPROVEN")
    else:
        print("LIVE_PREDICTION=ABSTAIN")
        print("REASON=","NO_CURRENT_FORMULA_MATCH" if not best["match"] else "NO_POSITIVE_NET_EDGE")
    print("CERTIFIED=FALSE")
    print("EXECUTION_AUTHORITY=FALSE")
    return best

if __name__=="__main__": run()
