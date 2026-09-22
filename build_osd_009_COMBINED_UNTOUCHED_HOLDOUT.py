from pathlib import Path
ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_009_combined_untouched_holdout.py"
TEST=ROOT/"test_osd_009_COMBINED_UNTOUCHED_HOLDOUT.py"
MODULE=r"""from pathlib import Path
import json,math,statistics
ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_006_temporal_behavior_corpus.jsonl"
A=ROOT/"runtime/strategy_discovery/osd_007_behavioral_sequence_candidates.json"
B=ROOT/"runtime/strategy_discovery/osd_008_fingerprint_leadlag_candidates.json"
OUT=ROOT/"runtime/strategy_discovery/osd_009_combined_holdout_results.json"
HURDLE=.02; SPLIT=.65; MIN_N=12; MIN_T=3
rows=[json.loads(x) for x in SRC.open(encoding="utf-8") if x.strip()]
rows.sort(key=lambda r:r["decision_epoch"]); hold=rows[int(len(rows)*SPLIT):]
cands=(json.loads(A.read_text(encoding="utf-8")).get("candidates") or [])+(json.loads(B.read_text(encoding="utf-8")).get("candidates") or [])
def match(r,cs):
    for c in cs:
        v=r.get(c["feature"])
        if not isinstance(v,(int,float)) or not math.isfinite(float(v)):return False
        if c["op"]=="LE" and v>c["threshold"]:return False
        if c["op"]=="GE" and v<c["threshold"]:return False
    return True
def stat(rs,d):
    z=[((float(r["future_return"]) if d=="UP" else -float(r["future_return"]))-HURDLE) for r in rs]
    if not z:return None
    m=sum(z)/len(z); sd=statistics.stdev(z) if len(z)>1 else 0
    return {"n":len(z),"tickers":len({r["ticker"] for r in rs}),"mean_net":m,"lb95":m-1.96*sd/math.sqrt(len(z)),
            "positive_rate":sum(x>0 for x in z)/len(z),"cumulative_net":sum(z)}
res=[]; winners=[]
for i,c in enumerate(cands):
    rs=[r for r in hold if r["horizon_seconds"]==c["horizon_seconds"] and match(r,c["conditions"])]
    s=stat(rs,c["direction"])
    z={"candidate_index":i,**c,"holdout":s,"winner":False}
    if s and s["n"]>=MIN_N and s["tickers"]>=MIN_T and s["lb95"]>0:
        z["winner"]=True; winners.append(z)
    res.append(z)
winners.sort(key=lambda x:(x["holdout"]["lb95"],x["holdout"]["mean_net"]),reverse=True)
OUT.write_text(json.dumps({"revision":"OSD-009-V1","hurdle":HURDLE,"holdout_rows":len(hold),"candidate_count":len(cands),"winner_count":len(winners),"winners":winners,"results":res},indent=2),encoding="utf-8")
print("[UNTOUCHED HOLDOUT ROWS]",len(hold))
print("[COMBINED CANDIDATES]",len(cands))
print("[HOLDOUT WINNERS]",len(winners))
for w in winners[:20]:
    s=w["holdout"]; print("[WINNER]",w["family"],"H=",w["horizon_seconds"],"DIR=",w["direction"],"N=",s["n"],"TICKERS=",s["tickers"],"MEAN_NET=",s["mean_net"],"LB95=",s["lb95"],"COND=",w["conditions"])
print("[HURDLE]",HURDLE)
print("[RESULT]","ADVANCED_STRATEGY_EDGE_SURVIVES_UNTOUCHED_HOLDOUT" if winners else "NO_ADVANCED_STRATEGY_EDGE_SURVIVES_UNTOUCHED_HOLDOUT")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""
TESTCODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_009_combined_untouched_holdout.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert 's["lb95"]>0' in s and "HURDLE=.02" in s and "MIN_N=12" in s and "MIN_T=3" in s
print("[PASS] OSD-009 combined untouched holdout compiles")
print("[PASS] fixed 2% hurdle and conservative LB95 gate preserved")
"""
TARGET.write_text(MODULE,encoding="utf-8"); TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec"); compile(TESTCODE,str(TEST),"exec")
print("[PASS] OSD-009 combined untouched holdout installed")
print("[TARGET]",TARGET); print("[TEST]",TEST)
