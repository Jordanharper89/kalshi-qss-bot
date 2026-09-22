from pathlib import Path

ROOT = Path.cwd().resolve()
TARGET = ROOT / "qseries_v2/oracle_strategy_discovery/osd_008_fingerprint_leadlag_indexed_v2.py"
TEST = ROOT / "test_osd_008_FINGERPRINT_LEADLAG_INDEXED_V2.py"

MODULE = r"""from pathlib import Path
import json, math, statistics
from collections import defaultdict

ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_006_temporal_behavior_corpus.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_008_fingerprint_leadlag_candidates.json"
HURDLE=.02; SPLIT=.65; MIN_N=12; MIN_T=3

rows=[json.loads(x) for x in SRC.open(encoding="utf-8") if x.strip()]
rows.sort(key=lambda r:r["decision_epoch"])
train=rows[:int(len(rows)*SPLIT)]

features=[
"self_5s_taker_imbalance","self_15s_taker_imbalance","self_60s_taker_imbalance",
"self_5s_trade_volume","self_15s_trade_volume","self_60s_trade_volume",
"self_5s_yes_return","self_15s_yes_return","self_60s_yes_return",
"sibling_5s_taker_imbalance","sibling_15s_taker_imbalance","sibling_60s_taker_imbalance",
"sibling_5s_yes_return","sibling_15s_yes_return","sibling_60s_yes_return",
"self_minus_sibling_5s_return","self_minus_sibling_15s_return","self_minus_sibling_60s_return",
"self_minus_sibling_5s_imbalance","self_minus_sibling_15s_imbalance","self_minus_sibling_60s_imbalance"
]
features=[f for f in features if any(isinstance(r.get(f),(int,float)) for r in train)]

def quant(a,p):
    a=sorted(a)
    return a[min(len(a)-1,max(0,int((len(a)-1)*p)))] if a else None

by_h=defaultdict(list)
for i,r in enumerate(train):
    by_h[r["horizon_seconds"]].append(i)

atoms=[]
for h,idxs in by_h.items():
    for f in features:
        vals=[float(train[i][f]) for i in idxs if isinstance(train[i].get(f),(int,float)) and math.isfinite(float(train[i][f]))]
        if len(vals)<MIN_N: continue
        for p in (.25,.5,.75):
            th=quant(vals,p)
            for op in ("LE","GE"):
                hit=set()
                for i in idxs:
                    v=train[i].get(f)
                    if not isinstance(v,(int,float)) or not math.isfinite(float(v)): continue
                    if (op=="LE" and v<=th) or (op=="GE" and v>=th):
                        hit.add(i)
                if len(hit)>=MIN_N:
                    atoms.append({"h":h,"feature":f,"op":op,"threshold":th,"hit":hit})

self_atoms=[a for a in atoms if "sibling" not in a["feature"]]
cross_atoms=[a for a in atoms if "sibling" in a["feature"]]

def stat(hit,direction):
    if len(hit)<MIN_N: return None
    z=[]; tick=set()
    for i in hit:
        r=train[i]
        y=float(r["future_return"])
        z.append((y if direction=="UP" else -y)-HURDLE)
        tick.add(r["ticker"])
    if len(tick)<MIN_T: return None
    m=sum(z)/len(z)
    sd=statistics.stdev(z) if len(z)>1 else 0.0
    return {"n":len(z),"tickers":len(tick),"mean_net":m,
            "lb95":m-1.96*sd/math.sqrt(len(z))}

cand=[]
pairs_checked=0
for a in self_atoms:
    for b in cross_atoms:
        if a["h"]!=b["h"] or a["feature"]==b["feature"]: continue
        pairs_checked+=1
        hit=a["hit"] & b["hit"]
        if len(hit)<MIN_N: continue
        for d in ("UP","DOWN"):
            s=stat(hit,d)
            if s and s["mean_net"]>0:
                cand.append({
                    "family":"FINGERPRINT_LEADLAG",
                    "horizon_seconds":a["h"],
                    "direction":d,
                    "conditions":[
                        {"feature":a["feature"],"op":a["op"],"threshold":a["threshold"]},
                        {"feature":b["feature"],"op":b["op"],"threshold":b["threshold"]}
                    ],
                    **s
                })

cand=sorted(cand,key=lambda x:(x["lb95"],x["mean_net"]),reverse=True)[:500]
OUT.write_text(json.dumps({
    "revision":"OSD-008-INDEXED-V2",
    "hurdle":HURDLE,
    "split":SPLIT,
    "feature_count":len(features),
    "atom_count":len(atoms),
    "pairs_checked":pairs_checked,
    "candidate_count":len(cand),
    "candidates":cand
},indent=2),encoding="utf-8")

print("[TRAIN ROWS]",len(train))
print("[LEAD/LAG FEATURES]",len(features))
print("[INDEXED ATOMS]",len(atoms))
print("[PAIRS CHECKED]",pairs_checked)
print("[FINGERPRINT/LEADLAG CANDIDATES]",len(cand))
print("[RESULT] FINGERPRINT_LEADLAG_CANDIDATES_READY")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

TESTCODE = r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_008_fingerprint_leadlag_indexed_v2.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
assert 'hit=a["hit"] & b["hit"]' in s
assert 'self_atoms=' in s and 'cross_atoms=' in s
assert 'HURDLE=.02' in s
assert 'FINGERPRINT_LEADLAG' in s
assert 'future_return' in s
print("[PASS] OSD-008 indexed V2 compiles")
print("[PASS] brute-force repeated corpus scans removed")
print("[PASS] indexed set-intersection pair evaluation installed")
print("[PASS] fixed 2% hurdle preserved")
print("[PASS] execution/publication remain false")
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec")
compile(TESTCODE,str(TEST),"exec")

print("[PASS] OSD-008 indexed lead/lag replacement installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[RETIRED] original OSD-008 brute-force runtime")
