import json,statistics,time
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_002_live_event_worker import CoinbaseHFWorker
from qseries_v2.oracle_coinbase_high_frequency.chf_003_canonical_event_normalizer import normalize_journal
from qseries_v2.oracle_coinbase_high_frequency.chf_004_multihorizon_windows import materialize
from qseries_v2.oracle_coinbase_high_frequency.chf_001_foundation import runtime_dir

ROOT=Path.cwd()
d=runtime_dir(ROOT)
for name in ("raw_events.jsonl","canonical_events.jsonl","condition_windows.jsonl","worker_state.json"):
    p=d/name
    if p.exists(): p.unlink()

w=CoinbaseHFWorker(ROOT)
raw=w.run(max_seconds=20)
print("[RAW_JOURNAL]",raw)
nraw=sum(1 for _ in raw.open("r",encoding="utf-8")) if raw.exists() else 0
print("[RAW_MESSAGES]",nraw)
assert nraw>0,"NO_COINBASE_WEBSOCKET_MESSAGES"

ncanon=normalize_journal(ROOT)
print("[CANONICAL_EVENTS]",ncanon)
assert ncanon>0,"NO_CANONICAL_EVENTS"

nwin=materialize(ROOT)
print("[WINDOW_ROWS]",nwin)
assert nwin>=12,"EXPECTED_3_PRODUCTS_X_4_WINDOWS"

rows=[json.loads(x) for x in (d/"condition_windows.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
print("[WINDOW_COUNTS]",{w:sum(r.get("window_seconds")==w for r in rows) for w in (5,15,30,60)})
products=sorted(set(r.get("product_id") for r in rows))
print("[PRODUCTS]",products)

# Physical raw arrival-gap cadence.
times=[]
for line in raw.read_text(encoding="utf-8").splitlines():
    try:
        x=json.loads(line); s=x.get("received_at")
        if s: times.append(__import__("datetime").datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
    except Exception:pass
gaps=[b-a for a,b in zip(times,times[1:]) if b>a]
if gaps:
    print("[RAW_MEDIAN_GAP_S]",round(statistics.median(gaps),6))
    print("[RAW_GAPS_LT5]",sum(g<5 for g in gaps),"of",len(gaps))
    assert statistics.median(gaps)<5.0,"MEDIAN_RAW_CADENCE_NOT_SUB5S"
print("[PROBABILITY_ENABLED]",False)
print("[DIRECTION_ENABLED]",False)
print("[PUBLICATION_ALLOWED]",False)
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] CHF-005 physical Coinbase live cadence certification complete")
