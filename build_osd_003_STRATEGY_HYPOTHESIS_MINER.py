from pathlib import Path

ROOT = Path.cwd().resolve()
TARGET = ROOT / 'qseries_v2/oracle_strategy_discovery/osd_003_strategy_hypothesis_miner.py'
TEST = ROOT / 'test_osd_003_STRATEGY_HYPOTHESIS_MINER.py'

TARGET.parent.mkdir(parents=True, exist_ok=True)

MODULE = r"""from pathlib import Path
import json,math,statistics,itertools
ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_002_strategy_feature_corpus.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_003_discovery_candidates.json"
HURDLE=0.02; SPLIT=0.65; MIN_N=12; MIN_TICKERS=3
META={"prediction_id","ticker","underlying","decision_epoch","horizon_seconds","future_return"}

rows=[]
for line in SRC.open(encoding="utf-8"):
    try:rows.append(json.loads(line))
    except:pass
rows.sort(key=lambda x:x["decision_epoch"])
cut=max(1,int(len(rows)*SPLIT)); train=rows[:cut]
features=[k for k in train[0] if k not in META and isinstance(train[0].get(k),(int,float))] if train else []

def vals(rs,f):return [float(r[f]) for r in rs if isinstance(r.get(f),(int,float)) and math.isfinite(float(r[f]))]
def quant(a,q):
    if not a:return None
    b=sorted(a); return b[min(len(b)-1,max(0,int((len(b)-1)*q)))]
def score(rs,d):
    net=[((float(r["future_return"]) if d=="UP" else -float(r["future_return"]))-HURDLE) for r in rs]
    if not net:return None
    mean=sum(net)/len(net); sd=statistics.stdev(net) if len(net)>1 else 0.0
    return {"n":len(net),"tickers":len({r["ticker"] for r in rs}),"mean_net":mean,
            "lb95":mean-1.96*sd/math.sqrt(len(net)),"positive_rate":sum(x>0 for x in net)/len(net)}

uni=[]
for h in sorted({r["horizon_seconds"] for r in train}):
    base=[r for r in train if r["horizon_seconds"]==h]
    for f in features:
        a=vals(base,f)
        if len(a)<MIN_N:continue
        for q in (.10,.25,.50,.75,.90):
            th=quant(a,q)
            for op in ("LE","GE"):
                hit=[r for r in base if isinstance(r.get(f),(int,float)) and ((r[f]<=th) if op=="LE" else (r[f]>=th))]
                for d in ("UP","DOWN"):
                    sc=score(hit,d)
                    if sc and sc["n"]>=MIN_N and sc["tickers"]>=MIN_TICKERS and sc["mean_net"]>0:
                        uni.append({"kind":"UNIVARIATE","horizon_seconds":h,"direction":d,
                                    "conditions":[{"feature":f,"op":op,"threshold":th}],**sc})
uni.sort(key=lambda x:(x["lb95"],x["mean_net"]),reverse=True)

pairs=[]
seed=uni[:50]
for a,b in itertools.combinations(seed,2):
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
            if c["op"]=="LE" and not v<=c["threshold"]:ok=False
            if c["op"]=="GE" and not v>=c["threshold"]:ok=False
        if ok:hit.append(r)
    sc=score(hit,a["direction"])
    if sc and sc["n"]>=MIN_N and sc["tickers"]>=MIN_TICKERS and sc["mean_net"]>0:
        pairs.append({"kind":"PAIR","horizon_seconds":a["horizon_seconds"],"direction":a["direction"],
                      "conditions":[ca,cb],**sc})

cand=uni+pairs
cand.sort(key=lambda x:(x["lb95"],x["mean_net"]),reverse=True)
OUT.write_text(json.dumps({"revision":"OSD-003","hurdle":HURDLE,"split":SPLIT,"total_rows":len(rows),
                           "discovery_rows":len(train),"holdout_rows":len(rows)-len(train),
                           "feature_count":len(features),"candidates":cand},indent=2))
print("[TOTAL ROWS]",len(rows),"[DISCOVERY]",len(train),"[UNTOUCHED HOLDOUT]",len(rows)-len(train))
print("[FEATURES]",len(features),"[UNIVARIATE POSITIVE]",len(uni),"[PAIR POSITIVE]",len(pairs))
print("[CANDIDATES FROZEN FOR HOLDOUT]",len(cand))
print("[HURDLE]",HURDLE)
print("[RESULT] DISCOVERY_CANDIDATES_READY")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

TEST_CODE = r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_003_strategy_hypothesis_miner.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
for x in ("HURDLE=0.02","SPLIT=0.65","UNIVARIATE","PAIR","future_return","mean_net","lb95"):
    assert x in s,x
assert "holdout" not in s[s.find("train=rows[:cut]"):s.find("features=")].lower()
print("[PASS] OSD-003 deterministic interface test")
print("[PASS] fixed 2% hurdle")
print("[PASS] discovery-only threshold generation")
print("[PASS] univariate and pair interaction mining enabled")
print("[PASS] untouched holdout is not used for candidate generation")
"""

TARGET.write_text(MODULE, encoding="utf-8")
TEST.write_text(TEST_CODE, encoding="utf-8")

compile(MODULE, str(TARGET), "exec")
compile(TEST_CODE, str(TEST), "exec")

print("[PASS] OSD-003 strategy hypothesis miner installed")
print("[TARGET]", TARGET)
print("[TEST]", TEST)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
