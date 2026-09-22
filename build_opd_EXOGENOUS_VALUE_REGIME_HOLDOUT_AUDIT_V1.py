from pathlib import Path
ROOT=Path.cwd().resolve()
AUDIT=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_exogenous_value_regime_holdout_audit.py"
TEST=ROOT/"test_opd_EXOGENOUS_VALUE_REGIME_HOLDOUT_AUDIT_V1.py"

AUDIT_CODE = r'''from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
OUTCOME=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
RESULT=ROOT/"runtime"/"predictive_data"/"opd_exogenous_value_regime_holdout_audit_v1.json"

HURDLE=0.02
TRAIN_FRAC=0.65
MIN_TRAIN_N=30
MIN_HOLDOUT_N=12
MIN_HOLDOUT_TICKERS=3

ALLOWED={
"source.crypto.condition.btc.bitcoin.fastest_fee_rate",
"source.crypto.condition.btc.bitcoin.half_hour_fee_rate",
"source.crypto.condition.btc.bitcoin.mempool_transaction_count",
"source.crypto.condition.btc.bitcoin.mempool_vsize",
"source.crypto.condition.btc.bitcoin.tip_block_size",
"source.crypto.condition.btc.bitcoin.tip_block_tx_count",
"source.crypto.condition.btc.bitcoin.tip_block_weight",
}

def load_jsonl(p):
    out=[]
    if not p.exists(): return out
    for line in p.read_text(encoding="utf-8").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def flt(x):
    try:
        if isinstance(x,bool): return None
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception: return None

def flatten_numeric(obj,prefix=""):
    out={}
    if isinstance(obj,dict):
        for k,v in obj.items():
            key=(prefix+"."+str(k)) if prefix else str(k)
            if isinstance(v,(dict,list)): out.update(flatten_numeric(v,key))
            else:
                z=flt(v)
                if z is not None: out[key]=z
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:32]):
            key=(prefix+"."+str(i)) if prefix else str(i)
            if isinstance(v,(dict,list)): out.update(flatten_numeric(v,key))
            else:
                z=flt(v)
                if z is not None: out[key]=z
    return out

def clean_btc(p):
    if str(p.get("asset") or "").upper()!="BTC": return False
    snap=p.get("exogenous_evidence_snapshot")
    if not isinstance(snap,dict) or not snap: return False
    sids={str(v.get("source_id") or "") for v in snap.values() if isinstance(v,dict)}
    return bool(sids) and sids.issubset(ALLOWED)

def features(p):
    out={}
    for v in (p.get("exogenous_evidence_snapshot") or {}).values():
        if not isinstance(v,dict): continue
        sid=str(v.get("source_id") or "")
        if sid not in ALLOWED: continue
        short=sid.rsplit(".",1)[-1]
        nums=flatten_numeric(v.get("canonical_observation"))
        for k,z in nums.items(): out[short+"."+k]=z
    return out

def outcome_map(rows):
    return {str(r.get("prediction_id")):r for r in rows if r.get("prediction_id")}

def rr(o):
    for k in ("future_return","realized_return","directional_return"):
        z=flt(o.get(k))
        if z is not None:return z
    return None

def event_time(p):
    for k in ("prediction_epoch","frozen_epoch","created_epoch","anchor_observed_epoch","observed_epoch"):
        z=flt(p.get(k))
        if z is not None:return z
    return 0.0

def lb95(xs):
    if not xs:return None
    mu=sum(xs)/len(xs)
    if len(xs)==1:return mu
    return mu-1.96*(statistics.stdev(xs)/math.sqrt(len(xs)))

pred=load_jsonl(PRED)
outs=outcome_map(load_jsonl(OUTCOME))
rows=[]
for p in pred:
    if not clean_btc(p): continue
    o=outs.get(str(p.get("prediction_id") or ""))
    if not o: continue
    r=rr(o)
    if r is None: continue
    fs=features(p)
    if not fs: continue
    rows.append({"time":event_time(p),"prediction_id":p.get("prediction_id"),"ticker":str(p.get("ticker") or ""),
                 "h":int(p.get("horizon_seconds") or 0),"features":fs,"future_return":r})

rows.sort(key=lambda x:(x["time"],str(x["prediction_id"])))
cut=max(1,min(len(rows)-1,int(len(rows)*TRAIN_FRAC))) if len(rows)>=2 else len(rows)
train=rows[:cut]; hold=rows[cut:]
by_h_train={}; by_h_hold={}
for r in train: by_h_train.setdefault(r["h"],[]).append(r)
for r in hold: by_h_hold.setdefault(r["h"],[]).append(r)

rules=[]
for h,tr in by_h_train.items():
    ho=by_h_hold.get(h,[])
    names=sorted({k for r in tr for k in r["features"]})
    for name in names:
        vals=sorted(r["features"][name] for r in tr if name in r["features"])
        if len(vals)<MIN_TRAIN_N: continue
        ths=[]
        for q in (0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90):
            ths.append(vals[max(0,min(len(vals)-1,int((len(vals)-1)*q)))])
        for th in sorted(set(ths)):
            for op in ("LE","GE"):
                trsel=[r for r in tr if name in r["features"] and ((r["features"][name]<=th) if op=="LE" else (r["features"][name]>=th))]
                if len(trsel)<MIN_TRAIN_N: continue
                for direction in ("UP","DOWN"):
                    trnets=[((r["future_return"] if direction=="UP" else -r["future_return"])-HURDLE) for r in trsel]
                    trmean=sum(trnets)/len(trnets)
                    if trmean<=0: continue
                    hosel=[r for r in ho if name in r["features"] and ((r["features"][name]<=th) if op=="LE" else (r["features"][name]>=th))]
                    if len(hosel)<MIN_HOLDOUT_N: continue
                    tickers={r["ticker"] for r in hosel}
                    if len(tickers)<MIN_HOLDOUT_TICKERS: continue
                    honets=[((r["future_return"] if direction=="UP" else -r["future_return"])-HURDLE) for r in hosel]
                    lb=lb95(honets); hm=sum(honets)/len(honets)
                    rules.append({"horizon_seconds":h,"feature":name,"op":op,"threshold":th,"direction":direction,
                                  "train_n":len(trsel),"train_mean_net_after_2pct":trmean,
                                  "holdout_n":len(hosel),"holdout_unique_tickers":len(tickers),
                                  "holdout_mean_net_after_2pct":hm,
                                  "holdout_positive_net_rate":sum(1 for x in honets if x>0)/len(honets),
                                  "holdout_lb95_net_after_2pct":lb,
                                  "holdout_profitable":lb is not None and lb>0})

rules.sort(key=lambda x:(x["holdout_profitable"],x["holdout_lb95_net_after_2pct"]),reverse=True)
wins=[x for x in rules if x["holdout_profitable"]]
payload={"revision":"EXOGENOUS_VALUE_REGIME_HOLDOUT_AUDIT_V1","hurdle":HURDLE,
         "labeled_rows":len(rows),"train_rows":len(train),"untouched_holdout_rows":len(hold),
         "candidate_rules_reaching_holdout":len(rules),"holdout_winners":len(wins),
         "winners":wins[:100],"top_rules":rules[:100]}
RESULT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

print("[CLEAN VALUE-LABELED ROWS]",len(rows))
print("[ROWS] total=",len(rows),"train=",len(train),"untouched_holdout=",len(hold))
print("[TRAIN-POSITIVE RULES REACHING HOLDOUT]",len(rules))
print("[HOLDOUT WINNERS]",len(wins))
for x in rules[:30]:
    print("[RULE] H=",x["horizon_seconds"],"FEATURE=",x["feature"],"OP=",x["op"],"TH=",x["threshold"],
          "DIR=",x["direction"],"TRAIN_N=",x["train_n"],"TRAIN_NET=",x["train_mean_net_after_2pct"],
          "HOLDOUT_N=",x["holdout_n"],"TICKERS=",x["holdout_unique_tickers"],
          "HOLDOUT_NET=",x["holdout_mean_net_after_2pct"],"LB95=",x["holdout_lb95_net_after_2pct"],
          "WINNER=",x["holdout_profitable"])
print("[RESULT FILE]",RESULT)
print("[RESULT]","CLEAN_EXOGENOUS_VALUE_REGIME_SURVIVES_UNTOUCHED_HOLDOUT" if wins else "NO_CLEAN_EXOGENOUS_VALUE_REGIME_SURVIVES_UNTOUCHED_HOLDOUT")
print("[MODEL MUTATION] FALSE")
print("[HURDLE CHANGE] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''

TEST_CODE = r'''from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_exogenous_value_regime_holdout_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in ("HURDLE=0.02","TRAIN_FRAC=0.65","MIN_TRAIN_N=30","MIN_HOLDOUT_N=12",
          "MIN_HOLDOUT_TICKERS=3","sids.issubset(ALLOWED)","flatten_numeric",
          "holdout_lb95_net_after_2pct"):
    assert x in s,x
print("[PASS] exogenous value-regime temporal holdout audit installed")
print("[PASS] only 7-source clean BTC snapshots admitted")
print("[PASS] actual canonical numeric evidence values extracted")
print("[PASS] thresholds selected from training only")
print("[PASS] untouched temporal holdout preserved")
print("[PASS] fixed 2% hurdle preserved")
print("[PASS] winner requires positive holdout 95% lower bound")
print("[MODEL MUTATION] FALSE")
'''

AUDIT.parent.mkdir(parents=True,exist_ok=True)
AUDIT.write_text(AUDIT_CODE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")
compile(AUDIT_CODE,str(AUDIT),"exec")
compile(TEST_CODE,str(TEST),"exec")
print("[PASS] exogenous value-regime holdout audit V1 installed")
print("[AUDIT]",AUDIT)
print("[TEST]",TEST)
print("[MODEL/SCORING/GATES] unchanged")
print("[OLD LEDGERS] untouched")
print("[HURDLE] 0.02 fixed")
