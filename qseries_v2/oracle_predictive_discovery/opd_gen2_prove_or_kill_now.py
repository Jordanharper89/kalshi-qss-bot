from pathlib import Path
import json,time

execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False

MIN_BASELINE_N=500
MIN_TRIGGER_N=100
MIN_TICKERS=10
MIN_NET_EXPECTED=0.005
MIN_FAVORABLE_EXCURSION=0.03
MIN_REWARD_RISK=1.20
MAX_Q=0.05
MIN_LIFT_RETENTION=0.25

def _read_jsonl(path):
    out=[]
    if not path.exists(): return out
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try: out.append(json.loads(line))
                except Exception: pass
    return out

def _target(o,name):
    if name=="RETURN_POS": return float(o.get("future_return",0.0))>0
    if name=="RETURN_NEG": return float(o.get("future_return",0.0))<0
    if name=="UP_5C": return bool(o.get("hit_plus_05"))
    if name=="DOWN_5C": return bool(o.get("hit_minus_05"))
    if name=="UP_10C": return bool(o.get("hit_plus_10"))
    if name=="DOWN_10C": return bool(o.get("hit_minus_10"))
    return False

def _mean(xs):
    return sum(xs)/len(xs) if xs else None

def _safe_rr(fav,adv):
    if fav is None or adv is None: return None
    return fav/max(adv,1e-9)

def prove_or_kill(root=None):
    root=Path(root or Path.cwd()).resolve()
    rt=root/"runtime"/"predictive_data"
    freeze_path=rt/"opd_gen2_candidate_freeze.json"
    if not freeze_path.exists():
        raise RuntimeError("GEN2_FREEZE_MISSING")

    freeze=json.loads(freeze_path.read_text(encoding="utf-8"))
    activation=float(freeze["activation_epoch"])
    candidates=list(freeze.get("candidates") or [])
    if not candidates:
        raise RuntimeError("GEN2_CANDIDATE_MISSING")

    states=_read_jsonl(rt/"opd_gen2_post_freeze_state_ledger.jsonl")
    outcomes={x["state_id"]:x for x in _read_jsonl(rt/"opd_033_prospective_outcome_ledger.jsonl") if x.get("state_id")}

    all_post=all(float(s.get("observed_epoch",0.0))>activation for s in states)
    if not all_post:
        raise RuntimeError("GEN2_LEDGER_CONTAINS_PRE_FREEZE_STATE")

    results=[]
    for c in candidates:
        fid=c["family_id"]
        h=int(c["horizon_seconds"])
        target=c["target"]

        hs=[s for s in states if int(s.get("horizon_seconds",-1))==h]
        resolved=[(s,outcomes[s["state_id"]]) for s in hs if s.get("state_id") in outcomes]
        trig=[(s,o) for s,o in resolved if fid in (s.get("matched_family_ids") or [])]

        base_rate=_mean([1.0 if _target(o,target) else 0.0 for _,o in resolved])
        trig_rate=_mean([1.0 if _target(o,target) else 0.0 for _,o in trig])
        lift=(trig_rate-base_rate) if base_rate is not None and trig_rate is not None else None

        rets=[float(o.get("future_return",0.0)) for _,o in trig]
        mfes=[float(o.get("mfe",0.0)) for _,o in trig]
        maes=[-float(o.get("mae",0.0)) for _,o in trig]

        mean_ret=_mean(rets)
        net=(mean_ret-0.020) if mean_ret is not None else None
        mean_mfe=_mean(mfes)
        mean_mae=_mean(maes)
        rr=_safe_rr(mean_mfe,mean_mae)

        # Gen2 is a pre-declared regime-flip test. Historical sign disagreement selected it,
        # so certification here is strictly fresh post-freeze economics + breadth/support.
        checks={
            "baseline_n":len(resolved)>=MIN_BASELINE_N,
            "trigger_n":len(trig)>=MIN_TRIGGER_N,
            "ticker_breadth":len({s.get("ticker") for s,_ in trig if s.get("ticker")})>=MIN_TICKERS,
            "net_expected":net is not None and net>=MIN_NET_EXPECTED,
            "favorable_excursion":mean_mfe is not None and mean_mfe>=MIN_FAVORABLE_EXCURSION,
            "reward_risk":rr is not None and rr>=MIN_REWARD_RISK,
            "positive_target_lift":lift is not None and lift>0.0,
        }
        certified=all(checks.values())

        live_matches=[s for s in hs if fid in (s.get("matched_family_ids") or [])]
        live_matches.sort(key=lambda s:float(s.get("observed_epoch",0.0)),reverse=True)
        latest=live_matches[0] if live_matches else None

        results.append({
            "family_id":fid,
            "horizon_seconds":h,
            "target":target,
            "states":len(hs),
            "resolved_baseline_n":len(resolved),
            "resolved_trigger_n":len(trig),
            "trigger_tickers":len({s.get("ticker") for s,_ in trig if s.get("ticker")}),
            "baseline_rate":base_rate,
            "trigger_rate":trig_rate,
            "fresh_lift":lift,
            "mean_trigger_return":mean_ret,
            "net_expected_after_hurdle":net,
            "mean_favorable_excursion":mean_mfe,
            "mean_adverse_excursion":mean_mae,
            "reward_risk_proxy":rr,
            "checks":checks,
            "certified":certified,
            "latest_live_match":latest,
        })

    best=max(results,key=lambda x:(x["certified"],x["resolved_trigger_n"],x["net_expected_after_hurdle"] if x["net_expected_after_hurdle"] is not None else -999))

    print("="*104)
    print("ORACLE GEN2 PROVE OR KILL NOW")
    print("="*104)
    print("GENERATION=2")
    print("ACTIVATION_EPOCH=",activation)
    print("POST_FREEZE_STATES=",len(states))
    print("ALL_POST_FREEZE=",all_post)
    print("-"*104)
    print("FAMILY_ID=",best["family_id"])
    print("TARGET=",best["target"],"HORIZON_SECONDS=",best["horizon_seconds"])
    print("RESOLVED_BASELINE_N=",best["resolved_baseline_n"])
    print("RESOLVED_TRIGGER_N=",best["resolved_trigger_n"])
    print("TRIGGER_TICKERS=",best["trigger_tickers"])
    print("FRESH_LIFT=",best["fresh_lift"])
    print("MEAN_TRIGGER_RETURN=",best["mean_trigger_return"])
    print("NET_EXPECTED_AFTER_2PCT_HURDLE=",best["net_expected_after_hurdle"])
    print("MEAN_FAVORABLE_EXCURSION=",best["mean_favorable_excursion"])
    print("REWARD_RISK_PROXY=",best["reward_risk_proxy"])
    print("PASSED_CHECKS=",sum(best["checks"].values()),"/",len(best["checks"]))
    failed=[k for k,v in best["checks"].items() if not v]
    print("FAILED_CHECKS=",",".join(failed) if failed else "NONE")
    print("-"*104)

    latest=best["latest_live_match"]
    if best["certified"] and latest:
        direction="UP" if best["target"] in ("RETURN_POS","UP_5C","UP_10C") else "DOWN"
        print("ORACLE LIVE EDGE PROVEN")
        print("TICKER=",latest.get("ticker"))
        print("DIRECTION=",direction)
        print("HORIZON_SECONDS=",best["horizon_seconds"])
        print("ANCHOR_PRICE=",latest.get("anchor_price"))
        print("EXPECTED_NET_EDGE=",best["net_expected_after_hurdle"])
        print("FRESH_TRIGGER_N=",best["resolved_trigger_n"])
        print("FRESH_TRIGGER_TICKERS=",best["trigger_tickers"])
        print("CERTIFIED=TRUE")
        print("PROBABILITY_ENABLED=FALSE")
        print("PUBLICATION_ALLOWED=FALSE")
        print("EXECUTION_AUTHORITY=FALSE")
        verdict="PROVEN"
    elif best["certified"] and not latest:
        print("ORACLE EDGE CERTIFIED BUT NO CURRENT LIVE FORMULA MATCH")
        print("CERTIFIED=TRUE")
        print("LIVE_PREDICTION=ABSTAIN")
        print("EXECUTION_AUTHORITY=FALSE")
        verdict="CERTIFIED_NO_LIVE_MATCH"
    else:
        print("ORACLE HAS NO PROVEN PROFITABLE EDGE")
        print("CERTIFIED=FALSE")
        print("LIVE_PREDICTION=ABSTAIN")
        print("EXACT_REASON_FAILED=",",".join(failed) if failed else "NO_CURRENT_MATCH")
        print("EXECUTION_AUTHORITY=FALSE")
        verdict="NOT_PROVEN"

    artifact={
        "generated_epoch":time.time(),
        "generation":2,
        "activation_epoch":activation,
        "verdict":verdict,
        "best":best,
        "selection_reused":False,
        "execution_authority":False,
    }
    (rt/"opd_gen2_prove_or_kill_now.json").write_text(json.dumps(artifact,indent=2,sort_keys=True),encoding="utf-8")
    return artifact

if __name__=="__main__":
    prove_or_kill()
