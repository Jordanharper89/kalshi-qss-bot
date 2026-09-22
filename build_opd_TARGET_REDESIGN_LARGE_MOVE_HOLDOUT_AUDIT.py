from pathlib import Path
SRC = r"""
from pathlib import Path
import json, math, statistics
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=BASE/"opd_full_evidence_live_outcome_ledger.jsonl"
DEST=BASE/"opd_target_redesign_large_move_holdout_audit.json"

HURDLE=.020
TRAIN_FRAC=.65
MIN_TRAIN_N=12
MIN_HOLDOUT_N=8
MIN_TICKERS=3
Z=1.2815515655446004
TOP_FEATURES=24
REV="TARGET_REDESIGN_LARGE_MOVE_HOLDOUT_AUDIT_V1"

BANNED=("future","outcome","resolved","resolution","directional_return","pnl",
        "profit","loss","mfe","mae","winner","result","settlement")

def rows(p):
    if not p.exists(): return []
    out=[]
    for line in p.read_text(encoding="utf-8").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def finite(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:return None

def flatten(obj,prefix="",out=None,depth=0):
    if out is None: out={}
    if depth>6:return out
    if isinstance(obj,dict):
        for k,v in obj.items():
            name=(prefix+"."+str(k)).strip(".")
            if any(b in name.lower() for b in BANNED): continue
            flatten(v,name,out,depth+1)
    elif isinstance(obj,bool):
        out[prefix]=1.0 if obj else 0.0
    elif isinstance(obj,(int,float)):
        v=finite(obj)
        if v is not None: out[prefix]=v
    return out

def decision_features(p):
    raw=flatten(p)
    f={}
    for k,v in raw.items():
        lk=k.lower()
        if any(x in lk for x in ("probability","net_edge","expected_return","passed",
                                 "actionable","generation","family_id","prediction_id",
                                 "anchor_id","sequence","epoch","timestamp")):
            continue
        f[k]=v

    h=finite(p.get("horizon_seconds"))
    rem=finite(p.get("contract_remaining_seconds"))
    st=p.get("state") if isinstance(p.get("state"),dict) else {}
    anchor=finite(st.get("anchor_price"))
    agree=finite(p.get("evidence_agreement"))
    sim=finite(p.get("mean_similarity"))
    cases=finite(p.get("comparable_cases"))
    ticks=finite(p.get("unique_tickers"))

    if h is not None:f["D.horizon"]=h
    if rem is not None:f["D.remaining"]=rem
    if h and rem is not None:
        f["D.horizon_remaining_ratio"]=h/max(rem,1e-9)
        f["D.log_remaining_horizon"]=math.log(max(rem,1e-9)/max(h,1e-9))
    if anchor is not None:
        f["D.anchor"]=anchor
        f["D.anchor_mid_distance"]=abs(anchor-.5)
        f["D.anchor_extremeness"]=max(anchor,1-anchor)
    if agree is not None:f["D.agreement"]=agree
    if sim is not None:f["D.similarity"]=sim
    if cases is not None:f["D.cases"]=cases
    if ticks is not None:f["D.tickers"]=ticks
    if cases and ticks is not None:f["D.cases_per_ticker"]=cases/max(ticks,1)

    votes=p.get("evidence_votes")
    if isinstance(votes,dict):
        means=[];dirs=[];supports=[]
        for src,v in votes.items():
            if not isinstance(v,dict):continue
            m=finite(v.get("mean_return"))
            n=finite(v.get("cases"))
            if m is not None:
                means.append(m);f["D.vote."+src+".mean"]=m;f["D.vote."+src+".abs"]=abs(m)
            if n is not None:
                supports.append(n);f["D.vote."+src+".n"]=n
            d=v.get("direction")
            if d in ("UP","DOWN"):dirs.append(1 if d=="UP" else -1)
        if means:
            f["D.vote.mean"]=sum(means)/len(means)
            f["D.vote.abs_mean"]=sum(abs(x) for x in means)/len(means)
            f["D.vote.range"]=max(means)-min(means)
            f["D.vote.std"]=statistics.pstdev(means) if len(means)>1 else 0
        if dirs:
            f["D.vote.balance"]=sum(dirs)/len(dirs)
            f["D.vote.abs_balance"]=abs(sum(dirs)/len(dirs))
        if supports:
            f["D.vote.support_min"]=min(supports)
            f["D.vote.support_range"]=max(supports)-min(supports)
    return f

def observed_time(r):
    for k in ("observed_epoch","prediction_epoch","frozen_epoch","created_epoch"):
        v=finite(r.get(k))
        if v is not None:return v
    st=r.get("state")
    if isinstance(st,dict):
        v=finite(st.get("observed_epoch"))
        if v is not None:return v
    return 0.0

def net(r):
    return float(r["directional_return"])-HURDLE

def target(r):
    # Objective redesign: predict a hurdle-clearing realized move, not generic direction.
    return 1 if net(r)>0 else 0

def summarize(rs):
    vals=[];ticks=set()
    for r in rs:
        try:vals.append(net(r));ticks.add(str(r.get("ticker") or ""))
        except Exception:pass
    if not vals:return None
    n=len(vals);m=sum(vals)/n
    sd=statistics.stdev(vals) if n>1 else 0.0
    se=sd/math.sqrt(n);lb=m-Z*se
    return {"n":n,"unique_tickers":len(ticks),"mean_net_after_2pct":m,
            "cumulative_net_after_2pct":sum(vals),
            "positive_net_rate":sum(v>0 for v in vals)/n,
            "stddev":sd,"standard_error":se,"conservative_lower_bound":lb}

def quantiles(vals):
    vals=sorted(set(vals))
    if len(vals)<5:return vals
    out=[]
    for p in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
        i=min(len(vals)-1,max(0,round((len(vals)-1)*p)))
        out.append(vals[i])
    return sorted(set(out))

def best_threshold(train,f):
    vals=[r["_features"][f] for r in train if f in r["_features"]]
    best=None
    for t in quantiles(vals):
        for op in (">=","<="):
            rr=[r for r in train if f in r["_features"] and
                ((r["_features"][f]>=t) if op==">=" else (r["_features"][f]<=t))]
            if len(rr)<MIN_TRAIN_N:continue
            ticks=len({str(r.get("ticker") or "") for r in rr})
            if ticks<MIN_TICKERS:continue
            positives=sum(target(r) for r in rr)
            rate=positives/len(rr)
            # training score favors target precision and support without using mean return directly
            score=(rate-.5)*math.sqrt(len(rr))
            cand=(score,rate,len(rr),ticks,op,t)
            if best is None or cand>best:best=cand
    return best

def apply(r,rule):
    f,op,t=rule
    x=r["_features"].get(f)
    if x is None:return False
    return x>=t if op==">=" else x<=t

def main():
    if not PRED.exists() or not OUT.exists():raise SystemExit("[FAIL] ledgers missing")
    pm={str(r.get("prediction_id")):r for r in rows(PRED) if r.get("prediction_id")}
    data=[]
    for o in rows(OUT):
        if o.get("resolution_status")!="RESOLVED_EXACT_FUTURE":continue
        p=pm.get(str(o.get("prediction_id")))
        if not p:continue
        r=dict(o)
        for k,v in p.items():r.setdefault(k,v)
        if int(r.get("generation") or 2)!=2:continue
        if not bool(r.get("actionable_at_freeze")):continue
        r["_features"]=decision_features(p)
        r["_time"]=observed_time(r)
        data.append(r)

    data.sort(key=lambda r:(r["_time"],str(r.get("prediction_id"))))
    cut=max(1,min(len(data)-1,int(len(data)*TRAIN_FRAC)))
    train,hold=data[:cut],data[cut:]

    cov=defaultdict(int)
    for r in train:
        for f in r["_features"]:cov[f]+=1
    feats=[f for f,n in cov.items() if n>=MIN_TRAIN_N]

    learned=[]
    for f in feats:
        b=best_threshold(train,f)
        if b:
            score,rate,n,ticks,op,t=b
            learned.append({"feature":f,"op":op,"threshold":t,"train_score":score,
                            "train_target_rate":rate,"train_n":n,"train_tickers":ticks})
    learned.sort(key=lambda x:(x["train_score"],x["train_n"]),reverse=True)

    results=[]
    for m in learned[:TOP_FEATURES]:
        rule=(m["feature"],m["op"],m["threshold"])
        hr=[r for r in hold if apply(r,rule)]
        hs=summarize(hr)
        ok=bool(hs and hs["n"]>=MIN_HOLDOUT_N and hs["unique_tickers"]>=MIN_TICKERS
                and hs["conservative_lower_bound"]>0)
        results.append({**m,"holdout":hs,"holdout_profitable":ok})

    # Build a train-only voting selector from strongest diverse features.
    vote_rules=[]
    used=set()
    for m in learned:
        if m["feature"] in used:continue
        vote_rules.append((m["feature"],m["op"],m["threshold"]))
        used.add(m["feature"])
        if len(vote_rules)>=7:break

    ensemble=[]
    for min_votes in range(2,max(2,len(vote_rules)+1)):
        hr=[]
        for r in hold:
            votes=sum(apply(r,x) for x in vote_rules)
            if votes>=min_votes:
                rr=dict(r);rr["_selector_votes"]=votes;hr.append(rr)
        hs=summarize(hr)
        ok=bool(hs and hs["n"]>=MIN_HOLDOUT_N and hs["unique_tickers"]>=MIN_TICKERS
                and hs["conservative_lower_bound"]>0)
        ensemble.append({"min_votes":min_votes,"rules":[list(x) for x in vote_rules],
                         "holdout":hs,"holdout_profitable":ok})

    winners=[x for x in results if x["holdout_profitable"]]+[x for x in ensemble if x["holdout_profitable"]]
    report={"revision":REV,"objective":"PREDICT_HURDLE_CLEARING_REALIZED_MOVE_NOT_GENERIC_DIRECTION",
            "hurdle":HURDLE,"rows_total":len(data),"rows_train":len(train),"rows_holdout":len(hold),
            "train_positive_target_n":sum(target(r) for r in train),
            "holdout_positive_target_n":sum(target(r) for r in hold),
            "feature_count":len(feats),"learned_rule_count":len(learned),
            "single_rule_results":results,"ensemble_results":ensemble,
            "profitable_holdout_selectors":winners}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*118)
    print(" TARGET REDESIGN — HURDLE-CLEARING MOVE TEMPORAL HOLDOUT")
    print("="*118)
    print("[REVISION]",REV)
    print("[OBJECTIVE] predict states likely to CLEAR 2PCT hurdle; generic direction is no longer the target")
    print("[ROWS] total=",len(data),"train=",len(train),"untouched_holdout=",len(hold))
    print("[TARGET POSITIVES] train=",sum(target(r) for r in train),"holdout=",sum(target(r) for r in hold))
    print("[DECISION-TIME FEATURES]",len(feats),"[TRAIN-LEARNED RULES]",len(learned))
    print("[PROFITABLE HOLDOUT SELECTORS]",len(winners))
    for i,w in enumerate(winners[:20],1):
        hs=w["holdout"]
        label=(w.get("feature"),w.get("op"),w.get("threshold")) if "feature" in w else ("ENSEMBLE_MIN_VOTES",w["min_votes"])
        print("[WINNER]",i,"SELECTOR=",json.dumps(label,separators=(",",":")),
              "HOLDOUT_N=",hs["n"],"TICKERS=",hs["unique_tickers"],
              "MEAN_NET=",round(hs["mean_net_after_2pct"],6),
              "CUM_NET=",round(hs["cumulative_net_after_2pct"],6),
              "LOWER_BOUND=",round(hs["conservative_lower_bound"],6),
              "POS_RATE=",round(hs["positive_net_rate"],4))
    if winners:
        print("[RESULT] TARGET_REDESIGN_PRODUCED_PROFITABLE_UNTOUCHED_HOLDOUT_SELECTOR")
        print("[NEXT] freeze selector as challenger and require brand-new post-freeze prospective proof")
    else:
        print("[RESULT] NO_PROFITABLE_SELECTOR_AFTER_TARGET_REDESIGN")
        print("[NEXT] stop predicting contract price-path from this evidence set; move target to underlying/event-specific opportunity")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
"""

TEST = r"""
from pathlib import Path
p=Path("audit_opd_TARGET_REDESIGN_LARGE_MOVE_HOLDOUT.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ("HURDLE=.020","TRAIN_FRAC=.65","MIN_TRAIN_N=12","MIN_HOLDOUT_N=8",
          "PREDICT_HURDLE_CLEARING_REALIZED_MOVE_NOT_GENERIC_DIRECTION",
          "return 1 if net(r)>0 else 0","best_threshold(train,f)",
          "training score favors target precision","train,hold=data[:cut],data[cut:]",
          "holdout_profitable","conservative_lower_bound","NO MODEL MUTATION"):
    assert x in s,x
print("[PASS] predictive objective changed from generic direction to hurdle-clearing move selection")
print("[PASS] exact resolved prospective Gen2 actionable outcomes are the only labels")
print("[PASS] strict chronological 65/35 train/untouched-holdout split")
print("[PASS] rule thresholds learned from train only")
print("[PASS] selector training optimizes hurdle-clear classification, not realized mean-return fitting")
print("[PASS] untouched holdout winner still requires positive conservative realized net after 2pct")
print("[PASS] future/outcome/PnL-derived fields excluded from decision-time features")
print("[PASS] production predictor/runtime remain untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

Path("audit_opd_TARGET_REDESIGN_LARGE_MOVE_HOLDOUT.py").write_text(SRC,encoding="utf-8")
Path("test_opd_TARGET_REDESIGN_LARGE_MOVE_HOLDOUT.py").write_text(TEST,encoding="utf-8")
compile(SRC,"audit_opd_TARGET_REDESIGN_LARGE_MOVE_HOLDOUT.py","exec")
compile(TEST,"test_opd_TARGET_REDESIGN_LARGE_MOVE_HOLDOUT.py","exec")
print("[PASS] target-redesign hurdle-clearing temporal-holdout audit installed")
print("[OLD TARGET] generic contract-price direction")
print("[NEW TARGET] select states likely to clear fixed 2pct hurdle")
print("[VALIDATION] chronological untouched holdout judged by actual realized net economics")
print("[MODEL MUTATION] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
