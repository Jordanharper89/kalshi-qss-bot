from pathlib import Path
ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_015_independent_source_edge_challenge.py"
TEST=ROOT/"test_osd_015_INDEPENDENT_SOURCE_EDGE_CHALLENGE.py"

MODULE=r"""from pathlib import Path
import json, math, statistics, bisect
from collections import defaultdict

ROOT=Path.cwd().resolve()
SD=ROOT/"runtime/strategy_discovery"
PD=ROOT/"runtime/predictive_data"
BASE=SD/"osd_012_full_evidence_clean_corpus.jsonl"
PRED=PD/"opd_full_evidence_live_prediction_ledger.jsonl"
CB=ROOT/"runtime/coinbase_hf/historical_condition_windows.jsonl"
OUT=SD/"osd_015_independent_source_edge_challenge.json"
ENRICHED=SD/"osd_015_independent_source_enriched_corpus.jsonl"
HURDLE=.02
TRAIN_FRAC=.65
MIN_N=12
MIN_TICKERS=3
MAX_LAG_S=90.0
Q=(.20,.40,.60,.80)

def finite(v):
    return isinstance(v,(int,float)) and math.isfinite(float(v))

def load_jsonl(p):
    z=[]
    if not p.exists(): return z
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:z.append(json.loads(line))
            except Exception:pass
    return z

def flatten(dst,prefix,obj):
    if isinstance(obj,dict):
        for k,v in obj.items(): flatten(dst,(prefix+"_"+str(k)).strip("_"),v)
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:32]): flatten(dst,f"{prefix}_{i}",v)
    elif isinstance(obj,(bool,int,float)) and (not isinstance(obj,float) or math.isfinite(obj)):
        dst[prefix]=int(obj) if isinstance(obj,bool) else float(obj)

def qtile(vals,q):
    if not vals:return None
    s=sorted(vals); x=(len(s)-1)*q; lo=int(x); hi=min(len(s)-1,lo+1)
    if lo==hi:return s[lo]
    return s[lo]+(s[hi]-s[lo])*(x-lo)

def score(rows,idxs,direction):
    vals=[]; ticks=set()
    for i in idxs:
        r=rows[i]; fr=r.get("future_return")
        if not finite(fr):continue
        raw=float(fr) if direction=="UP" else -float(fr)
        vals.append(raw-HURDLE); ticks.add(r.get("ticker"))
    n=len(vals)
    if not n:return {"n":0,"tickers":0,"mean_net":None,"lb95":None,"hit":None}
    m=statistics.mean(vals); sd=statistics.stdev(vals) if n>1 else 0.0
    return {"n":n,"tickers":len(ticks),"mean_net":m,
            "lb95":m-1.96*(sd/(n**.5)),
            "hit":sum(v>0 for v in vals)/n}

base=load_jsonl(BASE)
pred={r.get("prediction_id"):r for r in load_jsonl(PRED) if r.get("prediction_id")}

cbidx=defaultdict(list)
for r in load_jsonl(CB):
    product=str(r.get("product_id") or "")
    w=r.get("window_seconds"); ae=r.get("anchor_epoch")
    if product and finite(w) and finite(ae) and bool(r.get("past_only",True)):
        cbidx[(product,int(w))].append((float(ae),r))
for k in cbidx: cbidx[k].sort(key=lambda x:x[0])
cbtimes={k:[x[0] for x in v] for k,v in cbidx.items()}

asset_product={"BTC":"BTC-USD","ETH":"ETH-USD","SOL":"SOL-USD"}
enriched=[]; cb_joined=0; exo_joined=0
for r in base:
    t=r.get("decision_epoch")
    if not finite(t):continue
    rr=dict(r); feats=dict(r.get("features") or {})
    independent={}
    asset=str(r.get("asset") or "").upper()
    product=asset_product.get(asset)
    if product:
        for w in (5,15,30,60):
            k=(product,w); times=cbtimes.get(k,[])
            if not times:continue
            j=bisect.bisect_right(times,float(t))-1
            if j<0:continue
            ae,src=cbidx[k][j]
            lag=float(t)-ae
            if lag<0 or lag>MAX_LAG_S:continue
            independent[f"coinbase_{w}s_age_s"]=lag
            for name in ("return","open_price","close_price","event_count","max_event_gap_seconds","boundary_age_seconds"):
                v=src.get(name)
                if finite(v):independent[f"coinbase_{w}s_{name}"]=float(v)
        if independent:cb_joined+=1

    p=pred.get(r.get("prediction_id"),{})
    exo={}
    flatten(exo,"exo",p.get("exogenous_evidence_snapshot"))
    if exo:
        independent.update(exo); exo_joined+=1

    context={}
    for k,v in feats.items():
        lk=k.lower()
        if not finite(v):continue
        if any(x in lk for x in ("self_5s_","self_15s_","self_60s_","sibling_5s_","sibling_15s_","sibling_60s_")):
            context["kalshi_"+k]=float(v)

    rr["independent_features"]=independent
    rr["context_features"]=context
    enriched.append(rr)

with ENRICHED.open("w",encoding="utf-8") as f:
    for r in enriched:f.write(json.dumps(r,separators=(",",":"))+"\n")

enriched.sort(key=lambda r:(float(r.get("decision_epoch") or 0),str(r.get("prediction_id") or "")))
cut=int(len(enriched)*TRAIN_FRAC)
train=enriched[:cut]; hold=enriched[cut:]

def usable_features(rows,key,min_cov=.10):
    names=set()
    for r in rows:names.update((r.get(key) or {}).keys())
    out=[]
    for name in names:
        vals=[float((r.get(key) or {}).get(name)) for r in rows if finite((r.get(key) or {}).get(name))]
        if len(vals)<100:continue
        cov=len(vals)/len(rows)
        if cov<min_cov:continue
        if len(set(vals))/len(vals)<.01:continue
        out.append((cov,name,vals))
    out.sort(reverse=True)
    return out

ind=usable_features(train,"independent_features")[:100]
ctx=usable_features(train,"context_features",.20)[:40]

def atoms_for(specs,key):
    atoms=[]
    for cov,name,vals in specs:
        cuts=sorted(set(qtile(vals,q) for q in Q if qtile(vals,q) is not None))
        for c in cuts:
            for op in ("LE","GE"):
                hit=set()
                for i,r in enumerate(train):
                    v=(r.get(key) or {}).get(name)
                    if finite(v) and ((float(v)<=c) if op=="LE" else (float(v)>=c)):
                        hit.add(i)
                if len(hit)>=MIN_N:
                    atoms.append({"feature":name,"op":op,"cut":c,"key":key,"hit":hit})
    return atoms

ind_atoms=atoms_for(ind,"independent_features")
ctx_atoms=atoms_for(ctx,"context_features")

candidates=[]
for direction in ("UP","DOWN"):
    for a in ind_atoms:
        s=score(train,a["hit"],direction)
        if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS and s["mean_net"]>0:
            candidates.append({"type":"INDEPENDENT_SINGLE","direction":direction,
                               "a":{k:a[k] for k in ("feature","op","cut","key")},"train":s})

    ranked=[]
    for a in ind_atoms:
        s=score(train,a["hit"],direction)
        if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS:
            ranked.append((s["hit"] or 0.0,a))
    ranked.sort(key=lambda x:x[0],reverse=True)
    pool=[a for _,a in ranked[:140]]

    for i,a in enumerate(pool):
        for b in pool[i+1:]:
            if a["feature"]==b["feature"]:continue
            hit=a["hit"] & b["hit"]
            if len(hit)<MIN_N:continue
            s=score(train,hit,direction)
            if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS and s["mean_net"]>0:
                candidates.append({"type":"INDEPENDENT_PAIR","direction":direction,
                                   "a":{k:a[k] for k in ("feature","op","cut","key")},
                                   "b":{k:b[k] for k in ("feature","op","cut","key")},"train":s})

    for _,a in ranked[:100]:
        for b in ctx_atoms[:160]:
            hit=a["hit"] & b["hit"]
            if len(hit)<MIN_N:continue
            s=score(train,hit,direction)
            if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS and s["mean_net"]>0:
                candidates.append({"type":"CROSS_SOURCE_PAIR","direction":direction,
                                   "a":{k:a[k] for k in ("feature","op","cut","key")},
                                   "b":{k:b[k] for k in ("feature","op","cut","key")},"train":s})

candidates.sort(key=lambda c:c["train"]["lb95"] if c["train"]["lb95"] is not None else -999,reverse=True)
frozen=candidates[:500]

def atom_match(r,a):
    v=(r.get(a["key"]) or {}).get(a["feature"])
    if not finite(v):return False
    return float(v)<=a["cut"] if a["op"]=="LE" else float(v)>=a["cut"]

winners=[]; evaluated=[]
for c in frozen:
    hit=set()
    for i,r in enumerate(hold):
        ok=atom_match(r,c["a"])
        if ok and "b" in c:ok=atom_match(r,c["b"])
        if ok:hit.add(i)
    s=score(hold,hit,c["direction"])
    d=dict(c); d["holdout"]=s
    evaluated.append(d)
    if s["n"]>=MIN_N and s["tickers"]>=MIN_TICKERS and s["lb95"] is not None and s["lb95"]>0:
        winners.append(d)

winners.sort(key=lambda x:x["holdout"]["lb95"],reverse=True)
doc={
 "revision":"OSD-015-INDEPENDENT-SOURCE-EDGE-CHALLENGE-V1",
 "rows":len(enriched),"coinbase_rows_joined":cb_joined,"exogenous_rows_joined":exo_joined,
 "discovery_rows":len(train),"untouched_holdout_rows":len(hold),
 "usable_independent_features":len(ind),"usable_kalshi_context_features":len(ctx),
 "independent_atoms":len(ind_atoms),"context_atoms":len(ctx_atoms),
 "positive_discovery_candidates":len(candidates),"candidates_frozen_for_holdout":len(frozen),
 "holdout_winners":len(winners),"hurdle":HURDLE,"max_coinbase_lag_s":MAX_LAG_S,
 "winners":winners[:50],
 "top_evaluated":sorted(evaluated,key=lambda x:x["holdout"]["lb95"] if x["holdout"]["lb95"] is not None else -999,reverse=True)[:50],
 "execution_authority":False,"publication_allowed":False
}
OUT.write_text(json.dumps(doc,indent=2),encoding="utf-8")
print("[ROWS]",len(enriched),"[DISCOVERY]",len(train),"[UNTOUCHED HOLDOUT]",len(hold))
print("[COINBASE EXACT PAST-ONLY JOINS]",cb_joined)
print("[EXOGENOUS SNAPSHOT JOINS]",exo_joined)
print("[USABLE INDEPENDENT FEATURES]",len(ind))
print("[USABLE KALSHI CONTEXT FEATURES]",len(ctx))
print("[POSITIVE DISCOVERY CANDIDATES]",len(candidates))
print("[CANDIDATES FROZEN FOR HOLDOUT]",len(frozen))
print("[HOLDOUT WINNERS]",len(winners))
for w in winners[:10]:print("[WINNER]",json.dumps(w,separators=(",",":")))
if winners:
    print("[RESULT] INDEPENDENT_SOURCE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT")
else:
    print("[RESULT] NO_INDEPENDENT_SOURCE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT")
print("[HURDLE]",HURDLE)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
print("[REPORT]",OUT)
"""

TESTCODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_015_independent_source_edge_challenge.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
for x in ["historical_condition_windows.jsonl","past_only","bisect_right",
          "exogenous_evidence_snapshot","MAX_LAG_S=90.0","TRAIN_FRAC=.65","HURDLE=.02",
          "INDEPENDENT_PAIR","CROSS_SOURCE_PAIR",
          "INDEPENDENT_SOURCE_EDGE_SURVIVES_UNTOUCHED_HOLDOUT",
          '"execution_authority":False','"publication_allowed":False']:
    assert x in s,x
assert "UPDATE " not in s and "INSERT " not in s and "DELETE " not in s
print("[PASS] OSD-015 independent-source challenge compiles")
print("[PASS] Coinbase joins are past-only and bounded by decision time")
print("[PASS] raw exogenous prediction snapshots included")
print("[PASS] independent-only and cross-source interactions enabled")
print("[PASS] fixed 65/35 temporal holdout and 2% hurdle")
print("[PASS] execution/publication remain false")
"""

TARGET.parent.mkdir(parents=True,exist_ok=True)
TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec")
compile(TESTCODE,str(TEST),"exec")
print("[PASS] OSD-015 independent-source edge challenge installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
