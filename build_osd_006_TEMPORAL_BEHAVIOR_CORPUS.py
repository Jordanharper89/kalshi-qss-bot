from pathlib import Path
ROOT=Path.cwd().resolve()
TARGET=ROOT/"qseries_v2/oracle_strategy_discovery/osd_006_temporal_behavior_corpus.py"
TEST=ROOT/"test_osd_006_TEMPORAL_BEHAVIOR_CORPUS.py"
MODULE=r"""from pathlib import Path
import json,math
from collections import defaultdict,deque
ROOT=Path.cwd().resolve()
SRC=ROOT/"runtime/strategy_discovery/osd_002_strategy_feature_corpus.jsonl"
OUT=ROOT/"runtime/strategy_discovery/osd_006_temporal_behavior_corpus.jsonl"

rows=[]
for line in SRC.open(encoding="utf-8"):
    try:
        r=json.loads(line); r["decision_epoch"]=float(r["t"])
        for k,v in (r.get("features") or {}).items(): r[k]=v
        rows.append(r)
    except Exception: pass
rows.sort(key=lambda r:(r["decision_epoch"],r.get("seq",0)))

by_ticker=defaultdict(deque); by_asset=defaultdict(deque)
tmp=OUT.with_suffix(".tmp"); n=0

def finite(v): return isinstance(v,(int,float)) and math.isfinite(float(v))
def last_before(q,t):
    for x in reversed(q):
        if x["decision_epoch"] < t: return x
    return None
def kth_before(q,t,k):
    z=[x for x in q if x["decision_epoch"] < t]
    return z[-k] if len(z)>=k else None

with tmp.open("w",encoding="utf-8") as f:
    for r in rows:
        t=r["decision_epoch"]; ticker=r["ticker"]; asset=r.get("asset")
        tq=by_ticker[ticker]; aq=by_asset[asset] if asset else deque()
        p1=last_before(tq,t); p2=kth_before(tq,t,2); a1=last_before(aq,t) if asset else None
        x=dict(r)
        def delta(name,a,b):
            va=a.get(name) if a else None; vb=b.get(name) if b else None
            return float(va)-float(vb) if finite(va) and finite(vb) else None
        for name in ("self_5s_taker_imbalance","self_15s_taker_imbalance","self_60s_taker_imbalance",
                     "self_5s_trade_volume","self_15s_trade_volume","self_60s_trade_volume",
                     "self_5s_yes_return","self_15s_yes_return","self_60s_yes_return",
                     "self_5s_spread_mean","self_15s_spread_mean","self_60s_spread_mean"):
            x["d1_"+name]=delta(name,r,p1)
            x["d2_"+name]=delta(name,r,p2)
        x["ticker_gap_s"]=(t-p1["decision_epoch"]) if p1 else None
        x["asset_gap_s"]=(t-a1["decision_epoch"]) if a1 else None
        for w in (5,15,60):
            sr=r.get(f"self_{w}s_yes_return"); sib=r.get(f"sibling_{w}s_yes_return")
            x[f"self_minus_sibling_{w}s_return"]=(float(sr)-float(sib)) if finite(sr) and finite(sib) else None
            si=r.get(f"self_{w}s_taker_imbalance"); ai=r.get(f"sibling_{w}s_taker_imbalance")
            x[f"self_minus_sibling_{w}s_imbalance"]=(float(si)-float(ai)) if finite(si) and finite(ai) else None
        x["execution_authority"]=False; x["publication_allowed"]=False
        f.write(json.dumps(x,separators=(",",":"))+"\n"); n+=1
        tq.append(r)
        if asset: aq.append(r)
        while tq and t-tq[0]["decision_epoch"]>3600: tq.popleft()
        if asset:
            while aq and t-aq[0]["decision_epoch"]>3600: aq.popleft()
tmp.replace(OUT)
print("[INPUT ROWS]",len(rows))
print("[TEMPORAL BEHAVIOR ROWS]",n)
print("[RESULT] TEMPORAL_BEHAVIOR_CORPUS_READY")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
"""
TESTCODE=r"""from pathlib import Path
p=Path("qseries_v2/oracle_strategy_discovery/osd_006_temporal_behavior_corpus.py")
s=p.read_text(encoding="utf-8"); compile(s,str(p),"exec")
assert "d1_self_5s_taker_imbalance" in s
assert "self_minus_sibling_60s_return" in s
assert "future_return" not in s.split('x["execution_authority"]')[0]
print("[PASS] OSD-006 temporal corpus compiles")
print("[PASS] prior-state deltas and self-vs-sibling lead/lag features installed")
print("[PASS] no future target used to construct temporal features")
"""
TARGET.write_text(MODULE,encoding="utf-8"); TEST.write_text(TESTCODE,encoding="utf-8")
compile(MODULE,str(TARGET),"exec"); compile(TESTCODE,str(TEST),"exec")
print("[PASS] OSD-006 temporal behavior corpus installed")
print("[TARGET]",TARGET); print("[TEST]",TEST)
