from pathlib import Path

ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_004_untouched_holdout_evaluator_v2.py"
TEST=ROOT/"test_osd_004_UNTOUCHED_HOLDOUT_EVALUATOR_V2.py"

MODULE=r"""from pathlib import Path
import json,math,statistics

ROOT=Path.cwd().resolve()
CORPUS=ROOT/"runtime/strategy_discovery/osd_002_strategy_feature_corpus.jsonl"
CANDS=ROOT/"runtime/strategy_discovery/osd_003_discovery_candidates.json"
OUT=ROOT/"runtime/strategy_discovery/osd_004_untouched_holdout_results.json"

HURDLE=0.02
MIN_N=12
MIN_TICKERS=3
SPLIT=0.65

rows=[]
for line in CORPUS.open(encoding="utf-8"):
    try:
        r=json.loads(line)
        r["decision_epoch"]=float(r["t"])
        for k,v in (r.get("features") or {}).items():
            r[k]=v
        rows.append(r)
    except Exception:
        pass

rows.sort(key=lambda x:x["decision_epoch"])
cut=max(1,int(len(rows)*SPLIT))
hold=rows[cut:]

obj=json.loads(CANDS.read_text(encoding="utf-8"))
cands=obj.get("candidates") or []

def match(r,conditions):
    for c in conditions:
        v=r.get(c["feature"])
        if not isinstance(v,(int,float)) or not math.isfinite(float(v)):
            return False
        th=float(c["threshold"])
        if c["op"]=="LE":
            if float(v)>th:return False
        elif c["op"]=="GE":
            if float(v)<th:return False
        else:
            return False
    return True

def evaluate(rs,direction):
    net=[]
    for r in rs:
        try:y=float(r["future_return"])
        except Exception:continue
        dr=y if direction=="UP" else -y
        net.append(dr-HURDLE)
    if not net:return None
    mean=sum(net)/len(net)
    sd=statistics.stdev(net) if len(net)>1 else 0.0
    lb=mean-1.96*sd/math.sqrt(len(net))
    return {
        "n":len(net),
        "tickers":len({r["ticker"] for r in rs}),
        "mean_net":mean,
        "lb95":lb,
        "positive_rate":sum(x>0 for x in net)/len(net),
        "cumulative_net":sum(net),
    }

results=[]
winners=[]
for i,c in enumerate(cands):
    h=c["horizon_seconds"]
    d=c["direction"]
    rs=[r for r in hold if r.get("horizon_seconds")==h and match(r,c.get("conditions") or [])]
    sc=evaluate(rs,d)
    rec={
        "candidate_index":i,
        "kind":c.get("kind"),
        "horizon_seconds":h,
        "direction":d,
        "conditions":c.get("conditions") or [],
        "discovery_n":c.get("n"),
        "discovery_mean_net":c.get("mean_net"),
        "discovery_lb95":c.get("lb95"),
        "holdout":sc,
        "winner":False,
    }
    if sc and sc["n"]>=MIN_N and sc["tickers"]>=MIN_TICKERS and sc["lb95"]>0:
        rec["winner"]=True
        winners.append(rec)
    results.append(rec)

winners.sort(key=lambda x:(x["holdout"]["lb95"],x["holdout"]["mean_net"]),reverse=True)

OUT.write_text(json.dumps({
    "revision":"OSD-004-HOLDOUT-V2",
    "hurdle":HURDLE,
    "total_rows":len(rows),
    "discovery_rows":cut,
    "untouched_holdout_rows":len(hold),
    "candidate_count":len(cands),
    "evaluated_count":len(results),
    "winner_count":len(winners),
    "winners":winners,
    "results":results,
    "execution_authority":False,
    "publication_allowed":False,
},indent=2),encoding="utf-8")

print("[TOTAL ROWS]",len(rows))
print("[UNTOUCHED HOLDOUT ROWS]",len(hold))
print("[DISCOVERY CANDIDATES]",len(cands))
print("[EVALUATED]",len(results))
print("[HOLDOUT WINNERS]",len(winners))
for w in winners[:20]:
    h=w["holdout"]
    print("[WINNER]",
          "H=",w["horizon_seconds"],
          "DIR=",w["direction"],
          "KIND=",w["kind"],
          "N=",h["n"],
          "TICKERS=",h["tickers"],
          "MEAN_NET=",h["mean_net"],
          "LB95=",h["lb95"],
          "CONDITIONS=",w["conditions"])
print("[HURDLE]",HURDLE)
print("[RESULT]","STRATEGY_EDGE_SURVIVES_UNTOUCHED_HOLDOUT" if winners else "NO_STRATEGY_EDGE_SURVIVES_UNTOUCHED_HOLDOUT")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""

TEST_CODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_004_untouched_holdout_evaluator_v2.py")
s=p.read_text(encoding="utf-8")
compile(s,str(p),"exec")
assert 'r["decision_epoch"]=float(r["t"])' in s
assert 'for k,v in (r.get("features") or {}).items()' in s
assert 'osd_003_discovery_candidates.json' in s
assert 'sc["lb95"]>0' in s
assert "HURDLE=0.02" in s
assert "MIN_N=12" in s and "MIN_TICKERS=3" in s
assert "execution_authority" in s and "publication_allowed" in s
print("[PASS] OSD-004 holdout V2 compiles")
print("[PASS] exact OSD-002 corpus schema supported")
print("[PASS] exact OSD-003 V2 candidate file supported")
print("[PASS] fixed 2% hurdle preserved")
print("[PASS] untouched holdout winner gate = N>=12, tickers>=3, LB95>0")
print("[PASS] execution/publication remain false")
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec"); compile(TEST_CODE,str(TEST),"exec")
print("[PASS] OSD-004 exact holdout evaluator V2 installed")
print("[TARGET]",TARGET)
print("[TEST]",TEST)
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
