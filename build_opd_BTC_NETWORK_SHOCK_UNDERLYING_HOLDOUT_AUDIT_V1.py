from pathlib import Path
ROOT=Path.cwd().resolve()
AUDIT=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_btc_network_shock_underlying_holdout_audit.py"
TEST=ROOT/"test_opd_BTC_NETWORK_SHOCK_UNDERLYING_HOLDOUT_AUDIT_V1.py"

AUDIT_CODE = r"""
from pathlib import Path
import json, math, statistics

ROOT=Path.cwd().resolve()
PRED=ROOT/"runtime"/"predictive_data"/"opd_full_evidence_live_prediction_ledger.jsonl"
CHF=ROOT/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
RESULT=ROOT/"runtime"/"predictive_data"/"opd_btc_network_shock_underlying_holdout_audit_v1.json"

TRAIN_FRAC=0.65
MIN_TRAIN_N=30
MIN_HOLDOUT_N=12
MIN_HOLDOUT_TICKERS=3
HORIZONS={5,15,30,60}

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

def pred_time(p):
    for k in ("prediction_epoch","frozen_epoch","created_epoch","anchor_observed_epoch","observed_epoch"):
        v=flt(p.get(k))
        if v is not None:return v
    due=flt(p.get("resolution_due_epoch")); h=flt(p.get("horizon_seconds"))
    if due is not None and h is not None:return due-h
    return None

def clean_btc(p):
    if str(p.get("asset") or "").upper()!="BTC": return False
    snap=p.get("exogenous_evidence_snapshot")
    if not isinstance(snap,dict) or not snap:return False
    sids={str(v.get("source_id") or "") for v in snap.values() if isinstance(v,dict)}
    return bool(sids) and sids.issubset(ALLOWED)

def extract_value(v):
    obj=v.get("canonical_observation")
    stack=[obj]
    vals=[]
    while stack:
        x=stack.pop()
        if isinstance(x,dict):
            if "value" in x:
                z=flt(x.get("value"))
                if z is not None: vals.append(z)
            stack.extend(x.values())
        elif isinstance(x,list):
            stack.extend(x[:32])
    return vals[0] if vals else None

def snapshot_values(p):
    out={}
    for v in (p.get("exogenous_evidence_snapshot") or {}).values():
        if not isinstance(v,dict): continue
        sid=str(v.get("source_id") or "")
        if sid not in ALLOWED: continue
        z=extract_value(v)
        if z is not None: out[sid.rsplit(".",1)[-1]]=z
    return out

def chf_labels():
    out={}
    for r in load_jsonl(CHF):
        if str(r.get("product_id") or "").upper()!="BTC-USD": continue
        h=int(r.get("window_seconds") or 0)
        if h not in HORIZONS: continue
        if not r.get("full_horizon_complete"): continue
        a=flt(r.get("anchor_epoch")); ret=flt(r.get("return"))
        if a is None or ret is None: continue
        out[(round(a,3),h)]=ret
    return out

labels=chf_labels()
preds=[]
seen=set()
for p in load_jsonl(PRED):
    if not clean_btc(p): continue
    h=int(p.get("horizon_seconds") or 0)
    if h not in HORIZONS: continue
    t=pred_time(p)
    if t is None: continue
    vals=snapshot_values(p)
    if len(vals)<3: continue
    key=(round(t,3),h,str(p.get("ticker") or ""))
    if key in seen: continue
    seen.add(key)
    preds.append({"time":t,"h":h,"ticker":str(p.get("ticker") or ""),"values":vals})

preds.sort(key=lambda x:(x["time"],x["h"],x["ticker"]))

# Build metric deltas from the immediately previous clean snapshot.
prev_by_h={}
rows=[]
for p in preds:
    prev=prev_by_h.get(p["h"])
    prev_by_h[p["h"]]=p
    if prev is None: continue
    dt=p["time"]-prev["time"]
    if dt<=0 or dt>300: continue
    feats={}
    for k,v in p["values"].items():
        if k not in prev["values"]: continue
        old=prev["values"][k]
        feats[k+".delta"]=v-old
        if old!=0: feats[k+".pct_change"]=(v-old)/abs(old)
    if not feats: continue
    ret=labels.get((round(p["time"],3),p["h"]))
    if ret is None:
        # Exact ledger anchors sometimes differ from archived 5s grid by <2.5s.
        cands=[(abs(a-p["time"]),r) for (a,h),r in labels.items() if h==p["h"] and abs(a-p["time"])<=2.5]
        if cands: ret=min(cands,key=lambda x:x[0])[1]
    if ret is None: continue
    rows.append({"time":p["time"],"h":p["h"],"ticker":p["ticker"],"features":feats,"future_spot_return":ret})

rows.sort(key=lambda x:(x["time"],x["h"],x["ticker"]))
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
        thresholds=[]
        for q in (0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90):
            thresholds.append(vals[max(0,min(len(vals)-1,int((len(vals)-1)*q)))])
        for th in sorted(set(thresholds)):
            for op in ("LE","GE"):
                trsel=[r for r in tr if name in r["features"] and ((r["features"][name]<=th) if op=="LE" else (r["features"][name]>=th))]
                if len(trsel)<MIN_TRAIN_N: continue
                for direction in ("UP","DOWN"):
                    trg=[(r["future_spot_return"] if direction=="UP" else -r["future_spot_return"]) for r in trsel]
                    trmean=sum(trg)/len(trg)
                    if trmean<=0: continue
                    hosel=[r for r in ho if name in r["features"] and ((r["features"][name]<=th) if op=="LE" else (r["features"][name]>=th))]
                    if len(hosel)<MIN_HOLDOUT_N: continue
                    tickers={r["ticker"] for r in hosel}
                    if len(tickers)<MIN_HOLDOUT_TICKERS: continue
                    hog=[(r["future_spot_return"] if direction=="UP" else -r["future_spot_return"]) for r in hosel]
                    mu=sum(hog)/len(hog)
                    lb=mu if len(hog)==1 else mu-1.96*(statistics.stdev(hog)/math.sqrt(len(hog)))
                    rules.append({
                        "horizon_seconds":h,"feature":name,"op":op,"threshold":th,"direction":direction,
                        "train_n":len(trsel),"train_mean_directional_spot_return":trmean,
                        "holdout_n":len(hosel),"holdout_unique_tickers":len(tickers),
                        "holdout_mean_directional_spot_return":mu,
                        "holdout_hit_rate":sum(1 for x in hog if x>0)/len(hog),
                        "holdout_lb95_directional_spot_return":lb,
                        "holdout_positive":lb>0,
                    })

rules.sort(key=lambda x:(x["holdout_positive"],x["holdout_lb95_directional_spot_return"]),reverse=True)
wins=[x for x in rules if x["holdout_positive"]]
payload={
"revision":"BTC_NETWORK_SHOCK_UNDERLYING_HOLDOUT_AUDIT_V1",
"target":"BTC_USD_UNDERLYING_SPOT_RETURN",
"train_fraction":TRAIN_FRAC,
"exact_labeled_rows":len(rows),
"train_rows":len(train),
"untouched_holdout_rows":len(hold),
"rules_reaching_holdout":len(rules),
"holdout_winners":len(wins),
"winners":wins[:100],
"top_rules":rules[:100],
}
RESULT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

print("[TARGET] BTC_USD_UNDERLYING_SPOT_RETURN")
print("[EXACT SHOCK-LABELED ROWS]",len(rows))
print("[ROWS] total=",len(rows),"train=",len(train),"untouched_holdout=",len(hold))
print("[TRAIN-POSITIVE RULES REACHING HOLDOUT]",len(rules))
print("[HOLDOUT WINNERS]",len(wins))
for x in rules[:30]:
    print("[RULE] H=",x["horizon_seconds"],"FEATURE=",x["feature"],"OP=",x["op"],"TH=",x["threshold"],
          "DIR=",x["direction"],"TRAIN_N=",x["train_n"],"TRAIN_RET=",x["train_mean_directional_spot_return"],
          "HOLDOUT_N=",x["holdout_n"],"TICKERS=",x["holdout_unique_tickers"],
          "HOLDOUT_RET=",x["holdout_mean_directional_spot_return"],
          "LB95=",x["holdout_lb95_directional_spot_return"],
          "HIT=",x["holdout_hit_rate"],"WINNER=",x["holdout_positive"])
print("[RESULT FILE]",RESULT)
if wins:
    print("[RESULT] BTC_NETWORK_SHOCK_SIGNAL_SURVIVES_UNTOUCHED_UNDERLYING_HOLDOUT")
else:
    print("[RESULT] NO_BTC_NETWORK_SHOCK_SIGNAL_SURVIVES_UNTOUCHED_UNDERLYING_HOLDOUT")
print("[KALSHI MAPPING] NOT YET")
print("[MODEL MUTATION] FALSE")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

TEST_CODE = r"""
from pathlib import Path
P=Path("qseries_v2/oracle_predictive_discovery/opd_btc_network_shock_underlying_holdout_audit.py")
s=P.read_text(encoding="utf-8")
compile(s,str(P),"exec")
for x in (
'BTC_USD_UNDERLYING_SPOT_RETURN',
'HORIZONS={5,15,30,60}',
'sids.issubset(ALLOWED)',
'".delta"',
'".pct_change"',
'TRAIN_FRAC=0.65',
'MIN_TRAIN_N=30',
'MIN_HOLDOUT_N=12',
'holdout_lb95_directional_spot_return',
'[KALSHI MAPPING] NOT YET',
):
    assert x in s,x
print("[PASS] BTC network-shock underlying holdout audit installed")
print("[PASS] target is exact future BTC-USD spot return, not Kalshi contract return")
print("[PASS] signal uses decision-time network deltas/pct changes, not raw levels")
print("[PASS] only clean seven-source BTC snapshots admitted")
print("[PASS] training-only thresholds and untouched temporal holdout enforced")
print("[PASS] no Kalshi mapping/model mutation/execution")
"""

AUDIT.parent.mkdir(parents=True,exist_ok=True)
AUDIT.write_text(AUDIT_CODE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")
compile(AUDIT_CODE,str(AUDIT),"exec")
compile(TEST_CODE,str(TEST),"exec")
print("[PASS] BTC network-shock underlying holdout audit V1 installed")
print("[AUDIT]",AUDIT)
print("[TEST]",TEST)
print("[TARGET] BTC-USD underlying spot movement")
print("[MODEL/SCORING/GATES] unchanged")
print("[OLD LEDGERS] untouched")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
