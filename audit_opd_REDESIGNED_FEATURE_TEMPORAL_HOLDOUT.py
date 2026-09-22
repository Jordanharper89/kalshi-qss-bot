
from pathlib import Path
import json, math, statistics, itertools
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=BASE/"opd_full_evidence_live_outcome_ledger.jsonl"
DEST=BASE/"opd_redesigned_feature_temporal_holdout_audit.json"

HURDLE=.020
TRAIN_FRAC=.65
MIN_TRAIN_N=12
MIN_HOLDOUT_N=8
MIN_TICKERS=3
Z=1.2815515655446004
TOP_RULES=40
MAX_PAIR_SEED=18
REV="REDESIGNED_FEATURE_TEMPORAL_HOLDOUT_AUDIT_V1"

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

def pick(d,*needles):
    hits=[]
    for k,v in d.items():
        lk=k.lower()
        if all(n.lower() in lk for n in needles):
            hits.append((len(k),k,v))
    return sorted(hits)[0][2] if hits else None

def derive(p):
    raw=flatten(p)
    f=dict(raw)

    # Core market/time geometry.
    h=finite(p.get("horizon_seconds"))
    remain=finite(p.get("contract_remaining_seconds"))
    anchor=finite((p.get("state") or {}).get("anchor_price") if isinstance(p.get("state"),dict) else None)
    if h is not None:f["DERIVED.horizon_seconds"]=h
    if remain is not None:f["DERIVED.contract_remaining_seconds"]=remain
    if h and remain is not None:
        f["DERIVED.horizon_to_remaining_ratio"]=h/max(remain,1e-9)
        f["DERIVED.remaining_minus_horizon"]=remain-h
        f["DERIVED.log_remaining_over_horizon"]=math.log(max(remain,1e-9)/max(h,1e-9))
    if anchor is not None:
        f["DERIVED.anchor_price"]=anchor
        f["DERIVED.anchor_distance_mid"]=abs(anchor-.5)
        f["DERIVED.anchor_extremeness"]=max(anchor,1-anchor)
        if 0<anchor<1:f["DERIVED.anchor_logit"]=math.log(anchor/(1-anchor))

    # Current model meta-signals are legal frozen-at-decision features.
    prob=finite(p.get("predicted_probability"))
    edge=finite(p.get("net_edge_after_2pct"))
    agree=finite(p.get("evidence_agreement"))
    sim=finite(p.get("mean_similarity"))
    cases=finite(p.get("comparable_cases"))
    ticks=finite(p.get("unique_tickers"))
    if prob is not None:
        f["DERIVED.model_probability"]=prob
        f["DERIVED.model_confidence"]=abs(prob-.5)
    if edge is not None:f["DERIVED.model_net_edge"]=edge
    if agree is not None:f["DERIVED.evidence_agreement"]=agree
    if sim is not None:f["DERIVED.mean_similarity"]=sim
    if cases is not None:f["DERIVED.comparable_cases"]=cases
    if ticks is not None:f["DERIVED.unique_tickers"]=ticks
    if cases and ticks is not None:f["DERIVED.cases_per_ticker"]=cases/max(ticks,1.0)
    if prob is not None and agree is not None:
        f["DERIVED.confidence_x_agreement"]=abs(prob-.5)*agree
        f["DERIVED.confidence_minus_agreement"]=abs(prob-.5)-agree
    if edge is not None and prob is not None:
        f["DERIVED.edge_per_confidence"]=edge/max(abs(prob-.5),.01)

    # Vote structure from frozen evidence_votes.
    votes=p.get("evidence_votes")
    if isinstance(votes,dict):
        means=[]; dirs=[]; supports=[]
        for src,v in votes.items():
            if not isinstance(v,dict):continue
            m=finite(v.get("mean_return"))
            n=finite(v.get("cases"))
            if m is not None:
                means.append(m)
                f[f"DERIVED.vote_mean.{src}"]=m
                f[f"DERIVED.vote_abs_mean.{src}"]=abs(m)
            if n is not None:
                supports.append(n)
                f[f"DERIVED.vote_cases.{src}"]=n
            d=v.get("direction")
            if d in ("UP","DOWN"):
                dirs.append(1.0 if d=="UP" else -1.0)
        if means:
            f["DERIVED.vote_mean_avg"]=sum(means)/len(means)
            f["DERIVED.vote_mean_abs_avg"]=sum(abs(x) for x in means)/len(means)
            f["DERIVED.vote_mean_range"]=max(means)-min(means)
            f["DERIVED.vote_mean_std"]=statistics.pstdev(means) if len(means)>1 else 0.0
            f["DERIVED.vote_positive_fraction"]=sum(x>0 for x in means)/len(means)
        if dirs:
            f["DERIVED.direction_vote_balance"]=sum(dirs)/len(dirs)
            f["DERIVED.direction_vote_abs_balance"]=abs(sum(dirs)/len(dirs))
        if supports:
            f["DERIVED.vote_support_min"]=min(supports)
            f["DERIVED.vote_support_max"]=max(supports)
            f["DERIVED.vote_support_range"]=max(supports)-min(supports)
            f["DERIVED.vote_support_mean"]=sum(supports)/len(supports)

    # Cross-window shape: collect numeric frozen evidence names containing likely windows.
    by_prefix=defaultdict(list)
    for k,v in raw.items():
        lk=k.lower()
        if any(x in lk for x in ("coinbase","condition","learned","kalshi")):
            root=k.rsplit(".",1)[0] if "." in k else k
            by_prefix[root].append(v)
    for root,vals in by_prefix.items():
        vals=[finite(x) for x in vals]; vals=[x for x in vals if x is not None]
        if len(vals)>=2:
            tag="DERIVED.group."+str(abs(hash(root))%1000000)
            f[tag+".mean"]=sum(vals)/len(vals)
            f[tag+".std"]=statistics.pstdev(vals)
            f[tag+".range"]=max(vals)-min(vals)
            f[tag+".abs_mean"]=sum(abs(x) for x in vals)/len(vals)

    return f

def net(r): return float(r["directional_return"])-HURDLE

def summarize(rs):
    vals=[];ts=set()
    for r in rs:
        try: vals.append(net(r)); ts.add(str(r.get("ticker") or ""))
        except Exception: pass
    if not vals:return None
    n=len(vals);m=sum(vals)/n
    sd=statistics.stdev(vals) if n>1 else 0.0
    se=sd/math.sqrt(n);lb=m-Z*se
    return {"n":n,"unique_tickers":len(ts),"mean_net_after_2pct":m,
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

def apply(r,rule):
    f,op,t=rule
    x=r["_features"].get(f)
    if x is None:return False
    return x>=t if op==">=" else x<=t

def rtime(r):
    for k in ("observed_epoch","prediction_epoch","frozen_epoch","created_epoch"):
        v=finite(r.get(k))
        if v is not None:return v
    st=r.get("state")
    if isinstance(st,dict):
        v=finite(st.get("observed_epoch"))
        if v is not None:return v
    return 0.0

def main():
    if not PRED.exists() or not OUT.exists():raise SystemExit("[FAIL] prospective ledgers missing")
    pm={str(r.get("prediction_id")):r for r in rows(PRED) if r.get("prediction_id")}
    data=[]
    for o in rows(OUT):
        if o.get("resolution_status")!="RESOLVED_EXACT_FUTURE":continue
        p=pm.get(str(o.get("prediction_id")))
        if not p:continue
        r=dict(o)
        for k,v in p.items():r.setdefault(k,v)
        if int(r.get("generation") or 2)!=2 or not bool(r.get("actionable_at_freeze")):continue
        r["_features"]=derive(p);r["_time"]=rtime(r);data.append(r)

    data.sort(key=lambda r:(r["_time"],str(r.get("prediction_id"))))
    cut=max(1,min(len(data)-1,int(len(data)*TRAIN_FRAC)))
    train,hold=data[:cut],data[cut:]

    cov=defaultdict(int)
    for r in train:
        for f in r["_features"]:cov[f]+=1
    features=[f for f,n in cov.items() if n>=MIN_TRAIN_N and
              not any(b in f.lower() for b in BANNED)]

    cand=[]
    for f in features:
        vals=[r["_features"][f] for r in train if f in r["_features"]]
        for t in quantiles(vals):
            for op in (">=","<="):
                rr=[r for r in train if apply(r,(f,op,t))]
                s=summarize(rr)
                if s and s["n"]>=MIN_TRAIN_N and s["unique_tickers"]>=MIN_TICKERS:
                    cand.append(((f,op,t),s))
    cand.sort(key=lambda x:(x[1]["conservative_lower_bound"],x[1]["n"]),reverse=True)

    singles=[]
    for rule,ts in cand[:TOP_RULES]:
        hr=[r for r in hold if apply(r,rule)]
        hs=summarize(hr)
        ok=bool(hs and hs["n"]>=MIN_HOLDOUT_N and hs["unique_tickers"]>=MIN_TICKERS and hs["conservative_lower_bound"]>0)
        singles.append({"rule":list(rule),"train":ts,"holdout":hs,"holdout_positive":ok})

    seed=[x[0] for x in cand[:MAX_PAIR_SEED]]
    pairs=[]
    for a,b in itertools.combinations(seed,2):
        if a[0]==b[0]:continue
        tr=[r for r in train if apply(r,a) and apply(r,b)]
        ts=summarize(tr)
        if not ts or ts["n"]<MIN_TRAIN_N or ts["unique_tickers"]<MIN_TICKERS:continue
        hr=[r for r in hold if apply(r,a) and apply(r,b)]
        hs=summarize(hr)
        ok=bool(hs and hs["n"]>=MIN_HOLDOUT_N and hs["unique_tickers"]>=MIN_TICKERS and hs["conservative_lower_bound"]>0)
        pairs.append({"rules":[list(a),list(b)],"train":ts,"holdout":hs,"holdout_positive":ok})

    winners=[x for x in singles if x["holdout_positive"]]+[x for x in pairs if x["holdout_positive"]]
    winners.sort(key=lambda x:(x["holdout"]["conservative_lower_bound"],x["holdout"]["n"]),reverse=True)

    report={"revision":REV,"hurdle":HURDLE,"rows_total":len(data),"rows_train":len(train),
            "rows_holdout":len(hold),"redesigned_feature_count":len(features),
            "train_candidates":len(cand),"train_aggregate":summarize(train),
            "holdout_aggregate":summarize(hold),"positive_holdout_rules":winners,
            "single_results":singles,"pair_results":pairs[:100]}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*116);print(" REDESIGNED-FEATURE TEMPORAL HOLDOUT AUDIT");print("="*116)
    print("[REVISION]",REV)
    print("[ROWS] total=",len(data),"train=",len(train),"untouched_holdout=",len(hold))
    print("[REDESIGNED FEATURES]",len(features),"[TRAIN CANDIDATES]",len(cand))
    print("[HOLDOUT POSITIVE RULES]",len(winners))
    for i,w in enumerate(winners[:20],1):
        hs=w["holdout"];ts=w["train"];rule=w.get("rule") or w.get("rules")
        print("[WINNER]",i,"RULE=",json.dumps(rule,separators=(",",":")),
              "TRAIN_N=",ts["n"],"TRAIN_LB=",round(ts["conservative_lower_bound"],6),
              "HOLDOUT_N=",hs["n"],"TICKERS=",hs["unique_tickers"],
              "HOLDOUT_MEAN_NET=",round(hs["mean_net_after_2pct"],6),
              "HOLDOUT_LB=",round(hs["conservative_lower_bound"],6),
              "POS_RATE=",round(hs["positive_net_rate"],4))
    if winners:
        print("[RESULT] REDESIGNED_FEATURE_RULES_SURVIVE_TEMPORAL_HOLDOUT")
        print("[NEXT] freeze exact rule definition and start future prospective challenger")
    else:
        print("[RESULT] NO_REDESIGNED_FEATURE_RULE_SURVIVES_TEMPORAL_HOLDOUT")
        print("[NEXT] predictive target/contract-selection objective must be redesigned")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
