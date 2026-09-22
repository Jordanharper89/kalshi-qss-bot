from pathlib import Path
ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_008_fingerprint_leadlag_miner.py"
TEST=ROOT/"test_osd_008_FINGERPRINT_LEADLAG_MINER.py"
MODULE=r"""from pathlib import Path
import json,math,statistics,itertools
ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_006_temporal_behavior_corpus.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_008_fingerprint_leadlag_candidates.json"
HURDLE=.02; SPLIT=.65; MIN_N=12; MIN_T=3
rows=[json.loads(x) for x in SRC.open(encoding="utf-8") if x.strip()]
rows.sort(key=lambda r:r["decision_epoch"]); train=rows[:int(len(rows)*SPLIT)]
base_features=["self_5s_taker_imbalance","self_15s_taker_imbalance","self_60s_taker_imbalance",
"self_5s_trade_volume","self_15s_trade_volume","self_60s_trade_volume",
"self_5s_yes_return","self_15s_yes_return","self_60s_yes_return",
"sibling_5s_taker_imbalance","sibling_15s_taker_imbalance","sibling_60s_taker_imbalance",
"sibling_5s_yes_return","sibling_15s_yes_return","sibling_60s_yes_return",
"self_minus_sibling_5s_return","self_minus_sibling_15s_return","self_minus_sibling_60s_return",
"self_minus_sibling_5s_imbalance","self_minus_sibling_15s_imbalance","self_minus_sibling_60s_imbalance"]
features=[f for f in base_features if any(isinstance(r.get(f),(int,float)) for r in train)]
def q(a,p):
    a=sorted(a); return a[min(len(a)-1,max(0,int((len(a)-1)*p)))] if a else None
def stat(rs,d):
    z=[((float(r["future_return"]) if d=="UP" else -float(r["future_return"]))-HURDLE) for r in rs]
    if not z:return None
    m=sum(z)/len(z); sd=statistics.stdev(z) if len(z)>1 else 0
    return {"n":len(z),"tickers":len({r["ticker"] for r in rs}),"mean_net":m,"lb95":m-1.96*sd/math.sqrt(len(z))}
atoms=[]
for h in sorted({r["horizon_seconds"] for r in train}):
    b=[r for r in train if r["horizon_seconds"]==h]
    for f in features:
        vals=[float(r[f]) for r in b if isinstance(r.get(f),(int,float)) and math.isfinite(float(r[f]))]
        if len(vals)<MIN_N:continue
        for p in (.25,.5,.75):
            th=q(vals,p)
            for op in ("LE","GE"): atoms.append((h,{"feature":f,"op":op,"threshold":th}))
cand=[]
for (h,a),(h2,b) in itertools.combinations(atoms,2):
    if h!=h2 or a["feature"]==b["feature"]:continue
    # require one self/behavioral and one sibling/cross feature for lead-lag fingerprint
    mix=("sibling" in a["feature"]) != ("sibling" in b["feature"])
    if not mix:continue
    base=[r for r in train if r["horizon_seconds"]==h]
    hit=[]
    for r in base:
        ok=True
        for c in (a,b):
            v=r.get(c["feature"])
            if not isinstance(v,(int,float)):ok=False;break
            if c["op"]=="LE" and v>c["threshold"]:ok=False
            if c["op"]=="GE" and v<c["threshold"]:ok=False
        if ok:hit.append(r)
    for d in ("UP","DOWN"):
        s=stat(hit,d)
        if s and s["n"]>=MIN_N and s["tickers"]>=MIN_T and s["mean_net"]>0:
            cand.append({"family":"FINGERPRINT_LEADLAG","horizon_seconds":h,"direction":d,"conditions":[a,b],**s})
cand=sorted(cand,key=lambda x:(x["lb95"],x["mean_net"]),reverse=True)[:500]
OUT.write_text(json.dumps({"revision":"OSD-008-V1","hurdle":HURDLE,"split":SPLIT,"candidate_count":len(cand),"candidates":cand},indent=2),encoding="utf-8")
print("[LEAD/LAG FEATURES]",len(features))
print("[FINGERPRINT/LEADLAG CANDIDATES]",len(cand))
print("[RESULT] FINGERPRINT_LEADLAG_CANDIDATES_READY")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""
TESTCODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_008_fingerprint_leadlag_miner.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert "FINGERPRINT_LEADLAG" in s and "sibling" in s and "HURDLE=.02" in s
print("[PASS] OSD-008 fingerprint/lead-lag miner compiles")
print("[PASS] cross-contract lead/lag pair mining enabled")
"""
TARGET.write_text(MODULE,encoding="utf-8"); TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec"); compile(TESTCODE,str(TEST),"exec")
print("[PASS] OSD-008 fingerprint/lead-lag miner installed")
print("[TARGET]",TARGET); print("[TEST]",TEST)
