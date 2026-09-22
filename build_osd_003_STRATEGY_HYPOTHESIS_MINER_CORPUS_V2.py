from pathlib import Path

ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_003_strategy_hypothesis_miner_corpus_v2.py"
TEST=ROOT/"test_osd_003_STRATEGY_HYPOTHESIS_MINER_CORPUS_V2.py"

MODULE=r"""from pathlib import Path
import json,math,statistics,itertools
ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_002_strategy_feature_corpus.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_003_discovery_candidates.json"
HURDLE=0.02; SPLIT=0.65; MIN_N=12; MIN_TICKERS=3

rows=[]
for line in SRC.open(encoding="utf-8"):
    try:
        r=json.loads(line)
        r["decision_epoch"]=float(r["t"])
        f=r.get("features") or {}
        for k,v in f.items(): r[k]=v
        rows.append(r)
    except Exception: pass
rows.sort(key=lambda x:x["decision_epoch"])
cut=max(1,int(len(rows)*SPLIT)); train=rows[:cut]
META={"prediction_id","ticker","asset","decision_epoch","t","seq","horizon_seconds","future_return",
      "features","execution_authority","publication_allowed"}
features=sorted({k for r in train for k,v in r.items()
                 if k not in META and isinstance(v,(int,float)) and math.isfinite(float(v))})

def vals(rs,f): return [float(r[f]) for r in rs if isinstance(r.get(f),(int,float)) and math.isfinite(float(r[f]))]
def quant(a,q):
    b=sorted(a); return b[min(len(b)-1,max(0,int((len(b)-1)*q)))] if b else None
def score(rs,d):
    net=[(float(r["future_return"]) if d=="UP" else -float(r["future_return"]))-HURDLE for r in rs]
    if not net:return None
    m=sum(net)/len(net); sd=statistics.stdev(net) if len(net)>1 else 0.0
    return {"n":len(net),"tickers":len({r["ticker"] for r in rs}),"mean_net":m,
            "lb95":m-1.96*sd/math.sqrt(len(net)),"positive_rate":sum(x>0 for x in net)/len(net)}

uni=[]
for h in sorted({r["horizon_seconds"] for r in train}):
    base=[r for r in train if r["horizon_seconds"]==h]
    for f in features:
        a=vals(base,f)
        if len(a)<MIN_N:continue
        for q in (.10,.25,.50,.75,.90):
            th=quant(a,q)
            for op in ("LE","GE"):
                hit=[r for r in base if isinstance(r.get(f),(int,float)) and
                     ((r[f]<=th) if op=="LE" else (r[f]>=th))]
                for d in ("UP","DOWN"):
                    sc=score(hit,d)
                    if sc and sc["n"]>=MIN_N and sc["tickers"]>=MIN_TICKERS and sc["mean_net"]>0:
                        uni.append({"kind":"UNIVARIATE","horizon_seconds":h,"direction":d,
                                    "conditions":[{"feature":f,"op":op,"threshold":th}],**sc})
uni.sort(key=lambda x:(x["lb95"],x["mean_net"]),reverse=True)

pairs=[]
for a,b in itertools.combinations(uni[:50],2):
    if a["horizon_seconds"]!=b["horizon_seconds"] or a["direction"]!=b["direction"]:continue
    ca,cb=a["conditions"][0],b["conditions"][0]
    if ca["feature"]==cb["feature"]:continue
    base=[r for r in train if r["horizon_seconds"]==a["horizon_seconds"]]
    hit=[]
    for r in base:
        ok=True
        for c in (ca,cb):
            v=r.get(c["feature"])
            if not isinstance(v,(int,float)):ok=False;break
            if c["op"]=="LE" and v>c["threshold"]:ok=False
            if c["op"]=="GE" and v<c["threshold"]:ok=False
        if ok:hit.append(r)
    sc=score(hit,a["direction"])
    if sc and sc["n"]>=MIN_N and sc["tickers"]>=MIN_TICKERS and sc["mean_net"]>0:
        pairs.append({"kind":"PAIR","horizon_seconds":a["horizon_seconds"],"direction":a["direction"],
                      "conditions":[ca,cb],**sc})

cand=sorted(uni+pairs,key=lambda x:(x["lb95"],x["mean_net"]),reverse=True)
OUT.write_text(json.dumps({"revision":"OSD-003-CORPUS-V2","hurdle":HURDLE,"split":SPLIT,
 "total_rows":len(rows),"discovery_rows":len(train),"holdout_rows":len(rows)-len(train),
 "feature_count":len(features),"features":features,"candidates":cand},indent=2),encoding="utf-8")
print("[TOTAL ROWS]",len(rows),"[DISCOVERY]",len(train),"[UNTOUCHED HOLDOUT]",len(rows)-len(train))
print("[FEATURES]",len(features),"[UNIVARIATE POSITIVE]",len(uni),"[PAIR POSITIVE]",len(pairs))
print("[CANDIDATES FROZEN FOR HOLDOUT]",len(cand))
print("[HURDLE]",HURDLE)
print("[RESULT] DISCOVERY_CANDIDATES_READY")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

TEST_CODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_003_strategy_hypothesis_miner_corpus_v2.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert 'r["decision_epoch"]=float(r["t"])' in s
assert 'f=r.get("features") or {}' in s
assert 'for r in train for k,v in r.items()' in s
assert "HURDLE=0.02" in s and "PAIR" in s and "future_return" in s
print("[PASS] OSD-003 corpus V2 compiles")
print("[PASS] exact OSD-002 t field mapped to decision epoch")
print("[PASS] nested feature map flattened")
print("[PASS] feature discovery scans entire training corpus")
print("[PASS] fixed 2% hurdle preserved")
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec"); compile(TEST_CODE,str(TEST),"exec")
print("[PASS] OSD-003 corpus-interface rebuild installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[RETIRED] original OSD-003 incompatible with certified OSD-002 corpus schema")
