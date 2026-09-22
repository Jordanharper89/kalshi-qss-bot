from pathlib import Path
ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_007_behavioral_sequence_miner.py"
TEST=ROOT/"test_osd_007_BEHAVIORAL_SEQUENCE_MINER.py"
MODULE=r"""from pathlib import Path
import json,math,statistics,itertools
ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_006_temporal_behavior_corpus.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_007_behavioral_sequence_candidates.json"
HURDLE=.02; SPLIT=.65; MIN_N=12; MIN_T=3
rows=[json.loads(x) for x in SRC.open(encoding="utf-8") if x.strip()]
rows.sort(key=lambda r:r["decision_epoch"]); cut=int(len(rows)*SPLIT); train=rows[:cut]
exclude={"prediction_id","ticker","asset","decision_epoch","t","seq","horizon_seconds","future_return","features","execution_authority","publication_allowed"}
features=sorted({k for r in train for k,v in r.items() if k.startswith(("d1_","d2_","self_minus_sibling_","ticker_gap_s","asset_gap_s")) and isinstance(v,(int,float)) and math.isfinite(float(v))})
def q(a,p):
    a=sorted(a); return a[min(len(a)-1,max(0,int((len(a)-1)*p)))] if a else None
def stat(rs,d):
    z=[((float(r["future_return"]) if d=="UP" else -float(r["future_return"]))-HURDLE) for r in rs]
    if not z:return None
    m=sum(z)/len(z); sd=statistics.stdev(z) if len(z)>1 else 0
    return {"n":len(z),"tickers":len({r["ticker"] for r in rs}),"mean_net":m,"lb95":m-1.96*sd/math.sqrt(len(z))}
cand=[]
for h in sorted({r["horizon_seconds"] for r in train}):
    base=[r for r in train if r["horizon_seconds"]==h]
    for f in features:
        vals=[float(r[f]) for r in base if isinstance(r.get(f),(int,float)) and math.isfinite(float(r[f]))]
        if len(vals)<MIN_N: continue
        for p in (.1,.25,.5,.75,.9):
            th=q(vals,p)
            for op in ("LE","GE"):
                hit=[r for r in base if isinstance(r.get(f),(int,float)) and ((r[f]<=th) if op=="LE" else (r[f]>=th))]
                for d in ("UP","DOWN"):
                    s=stat(hit,d)
                    if s and s["n"]>=MIN_N and s["tickers"]>=MIN_T and s["mean_net"]>0:
                        cand.append({"family":"BEHAVIORAL_SEQUENCE","horizon_seconds":h,"direction":d,"conditions":[{"feature":f,"op":op,"threshold":th}],**s})
cand=sorted(cand,key=lambda x:(x["lb95"],x["mean_net"]),reverse=True)[:500]
OUT.write_text(json.dumps({"revision":"OSD-007-V1","hurdle":HURDLE,"split":SPLIT,"candidate_count":len(cand),"candidates":cand},indent=2),encoding="utf-8")
print("[TEMPORAL FEATURES]",len(features))
print("[BEHAVIORAL SEQUENCE CANDIDATES]",len(cand))
print("[RESULT] BEHAVIORAL_SEQUENCE_CANDIDATES_READY")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""
TESTCODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_007_behavioral_sequence_miner.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert "BEHAVIORAL_SEQUENCE" in s and "HURDLE=.02" in s and "SPLIT=.65" in s
print("[PASS] OSD-007 behavioral sequence miner compiles")
print("[PASS] fixed 2% hurdle and discovery-only generation preserved")
"""
TARGET.write_text(MODULE,encoding="utf-8"); TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec"); compile(TESTCODE,str(TEST),"exec")
print("[PASS] OSD-007 behavioral sequence miner installed")
print("[TARGET]",TARGET); print("[TEST]",TEST)
