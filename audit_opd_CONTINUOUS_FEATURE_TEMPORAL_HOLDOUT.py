
from pathlib import Path
import json, math, statistics
from collections import defaultdict

ROOT=Path.cwd().resolve()
BASE=ROOT/"runtime"/"predictive_data"
PRED=BASE/"opd_full_evidence_live_prediction_ledger.jsonl"
OUT=BASE/"opd_full_evidence_live_outcome_ledger.jsonl"
DEST=BASE/"opd_continuous_feature_temporal_holdout_audit.json"

HURDLE=.020
TRAIN_FRAC=.65
MIN_TRAIN_N=12
MIN_HOLDOUT_N=8
MIN_TICKERS=3
Z=1.2815515655446004
TOP_FEATURES=30
MAX_PAIRS=20
REV="CONTINUOUS_FEATURE_TEMPORAL_HOLDOUT_AUDIT_V1"

BANNED=("future","outcome","resolved","resolution","return","pnl","profit","loss","mfe","mae",
        "hit","winner","result","settlement","directional_return","net_realized")

def rows(p):
    if not p.exists(): return []
    out=[]
    for line in p.read_text(encoding="utf-8").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def flatten(obj,prefix="",out=None,depth=0):
    if out is None: out={}
    if depth>5:return out
    if isinstance(obj,dict):
        for k,v in obj.items():
            kk=str(k)
            name=(prefix+"."+kk).strip(".")
            low=name.lower()
            if any(x in low for x in BANNED): continue
            flatten(v,name,out,depth+1)
    elif isinstance(obj,(list,tuple)):
        # lists are deliberately excluded from threshold search
        pass
    elif isinstance(obj,bool):
        out[prefix]=1.0 if obj else 0.0
    elif isinstance(obj,(int,float)) and not isinstance(obj,bool):
        try:
            x=float(obj)
            if math.isfinite(x):out[prefix]=x
        except Exception:pass
    return out

def net(r):
    return float(r["directional_return"])-HURDLE

def summarize(rs):
    if not rs:return None
    vals=[];ticks=set()
    for r in rs:
        try:vals.append(net(r));ticks.add(str(r.get("ticker") or ""))
        except Exception:pass
    if not vals:return None
    n=len(vals);m=sum(vals)/n
    sd=statistics.stdev(vals) if n>1 else 0.0
    se=sd/math.sqrt(n)
    lb=m-Z*se
    return {"n":n,"unique_tickers":len(ticks),"mean_net_after_2pct":m,
            "cumulative_net_after_2pct":sum(vals),"positive_net_rate":sum(v>0 for v in vals)/n,
            "stddev":sd,"standard_error":se,"conservative_lower_bound":lb}

def quantiles(vals):
    vals=sorted(set(vals))
    if len(vals)<5:return vals
    qs=[]
    for p in (.10,.20,.30,.40,.50,.60,.70,.80,.90):
        i=min(len(vals)-1,max(0,round((len(vals)-1)*p)))
        qs.append(vals[i])
    return sorted(set(qs))

def apply_rule(r,rule):
    f,op,t=rule
    x=r["_features"].get(f)
    if x is None:return False
    return x>=t if op==">=" else x<=t

def key_time(r):
    for k in ("observed_epoch","prediction_epoch","frozen_epoch","created_epoch"):
        try:return float(r.get(k))
        except Exception:pass
    st=r.get("state")
    if isinstance(st,dict):
        try:return float(st.get("observed_epoch"))
        except Exception:pass
    return 0.0

def main():
    if not PRED.exists() or not OUT.exists():
        raise SystemExit("[FAIL] prospective ledgers missing")
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
        r["_features"]=flatten(p)
        r["_time"]=key_time(r)
        data.append(r)

    data.sort(key=lambda r:(r["_time"],str(r.get("prediction_id"))))
    if len(data)<40:raise SystemExit("[FAIL] insufficient resolved actionable rows")
    cut=max(1,min(len(data)-1,int(len(data)*TRAIN_FRAC)))
    train=data[:cut];hold=data[cut:]

    coverage=defaultdict(int)
    for r in train:
        for f in r["_features"]:coverage[f]+=1
    features=[f for f,n in coverage.items() if n>=MIN_TRAIN_N]
    # exclude identifiers/epochs/sequences and current model's own declared probability/edge
    features=[f for f in features if not any(x in f.lower() for x in
              ("prediction_id","anchor_id","sequence","epoch","timestamp","probability",
               "net_edge","expected_return","passed","actionable","generation","family_id"))]

    candidates=[]
    for f in features:
        vals=[r["_features"][f] for r in train if f in r["_features"]]
        for t in quantiles(vals):
            for op in (">=","<="):
                tr=[r for r in train if apply_rule(r,(f,op,t))]
                s=summarize(tr)
                if not s or s["n"]<MIN_TRAIN_N or s["unique_tickers"]<MIN_TICKERS:continue
                candidates.append(((f,op,t),s))
    candidates.sort(key=lambda x:(x[1]["conservative_lower_bound"],x[1]["n"]),reverse=True)

    selected=candidates[:TOP_FEATURES]
    singles=[]
    for rule,ts in selected:
        hr=[r for r in hold if apply_rule(r,rule)]
        hs=summarize(hr)
        singles.append({"rule":[rule[0],rule[1],rule[2]],"train":ts,"holdout":hs,
                        "holdout_positive":bool(hs and hs["n"]>=MIN_HOLDOUT_N and
                          hs["unique_tickers"]>=MIN_TICKERS and hs["conservative_lower_bound"]>0)})

    # Pair only strongest train rules; threshold definitions stay train-only.
    pair_seed=[x[0] for x in selected[:MAX_PAIRS]]
    pairs=[]
    for i in range(len(pair_seed)):
        for j in range(i+1,len(pair_seed)):
            a,b=pair_seed[i],pair_seed[j]
            if a[0]==b[0]:continue
            tr=[r for r in train if apply_rule(r,a) and apply_rule(r,b)]
            ts=summarize(tr)
            if not ts or ts["n"]<MIN_TRAIN_N or ts["unique_tickers"]<MIN_TICKERS:continue
            hr=[r for r in hold if apply_rule(r,a) and apply_rule(r,b)]
            hs=summarize(hr)
            pairs.append({"rules":[list(a),list(b)],"train":ts,"holdout":hs,
                          "holdout_positive":bool(hs and hs["n"]>=MIN_HOLDOUT_N and
                            hs["unique_tickers"]>=MIN_TICKERS and hs["conservative_lower_bound"]>0)})
    pairs.sort(key=lambda x:((x["holdout"]["conservative_lower_bound"] if x["holdout"] else -999),
                              x["holdout"]["n"] if x["holdout"] else 0),reverse=True)

    winners=[x for x in singles if x["holdout_positive"]]+[x for x in pairs if x["holdout_positive"]]
    report={"revision":REV,"hurdle":HURDLE,"train_fraction":TRAIN_FRAC,
            "rows_total":len(data),"rows_train":len(train),"rows_holdout":len(hold),
            "feature_count":len(features),"single_candidates_tested":len(candidates),
            "train_aggregate":summarize(train),"holdout_aggregate":summarize(hold),
            "single_results":singles,"pair_results":pairs[:100],
            "positive_temporal_holdout_rules":winners}
    DEST.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    print("="*116)
    print(" CONTINUOUS-FEATURE TEMPORAL HOLDOUT AUDIT")
    print("="*116)
    print("[REVISION]",REV)
    print("[ROWS] total=",len(data),"train=",len(train),"untouched_holdout=",len(hold))
    print("[FEATURES]",len(features),"[TRAIN-ONLY THRESHOLD CANDIDATES]",len(candidates))
    print("[HOLDOUT POSITIVE RULES]",len(winners))
    for i,w in enumerate(winners[:20],1):
        hs=w["holdout"]; ts=w["train"]
        rule=w.get("rule") or w.get("rules")
        print("[WINNER]",i,"RULE=",json.dumps(rule,separators=(",",":")),
              "TRAIN_N=",ts["n"],"TRAIN_LB=",round(ts["conservative_lower_bound"],6),
              "HOLDOUT_N=",hs["n"],"HOLDOUT_TICKERS=",hs["unique_tickers"],
              "HOLDOUT_MEAN_NET=",round(hs["mean_net_after_2pct"],6),
              "HOLDOUT_LB=",round(hs["conservative_lower_bound"],6))
    if winners:
        print("[RESULT] TEMPORAL_HOLDOUT_POSITIVE_FEATURE_RULES_FOUND")
        print("[NEXT] freeze selected rule(s) as challenger; certification still requires future post-freeze outcomes")
    else:
        print("[RESULT] NO_TEMPORAL_HOLDOUT_POSITIVE_FEATURE_RULE_FOUND")
        print("[NEXT] current evidence representation itself must be redesigned; do not tune thresholds")
    print("[AUDIT]",DEST)
    print("[NO MODEL MUTATION] TRUE")
    print("[EXECUTION/PUBLICATION] FALSE/FALSE")

if __name__=="__main__":main()
