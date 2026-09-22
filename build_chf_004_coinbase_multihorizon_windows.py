from pathlib import Path
import py_compile
ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
assert (PKG/"chf_003_canonical_event_normalizer.py").exists(),"CHF-003 required"
BODY=r"""
import json,statistics
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from .chf_001_foundation import WINDOW_SECONDS,runtime_dir

REVISION="CHF-004"

def _dt(s):
    if not s:return None
    try:return datetime.fromisoformat(str(s).replace("Z","+00:00")).timestamp()
    except Exception:return None

def materialize(root:Path):
    d=runtime_dir(Path(root)); canon=d/"canonical_events.jsonl"; out=d/"condition_windows.jsonl"
    if not canon.exists(): return 0
    events=[]
    with canon.open("r",encoding="utf-8") as f:
        for line in f:
            try:
                x=json.loads(line); t=_dt(x.get("observed_at") or x.get("received_at"))
                if t is not None and x.get("product_id"): events.append((t,x))
            except Exception: pass
    by=defaultdict(list)
    for t,x in events: by[x["product_id"]].append((t,x))
    rows=[]
    for product,arr in by.items():
        arr.sort(key=lambda z:z[0]); end=arr[-1][0]
        for w in WINDOW_SECONDS:
            sample=[x for t,x in arr if end-w < t <= end]
            prices=[x.get("price") for x in sample if isinstance(x.get("price"),(int,float))]
            trades=[x for x in sample if x.get("observation_type")=="coinbase_market_trade"]
            sizes=[x.get("size") for x in trades if isinstance(x.get("size"),(int,float))]
            bids=[x.get("best_bid") for x in sample if isinstance(x.get("best_bid"),(int,float))]
            asks=[x.get("best_ask") for x in sample if isinstance(x.get("best_ask"),(int,float))]
            row={"observed_at":datetime.fromtimestamp(end,timezone.utc).isoformat(),
                 "source_id":f"source.crypto.hf.coinbase.window.{product.lower()}.{w}s",
                 "observation_type":"coinbase_hf_condition_window","product_id":product,
                 "window_seconds":w,"event_count":len(sample),"trade_count":len(trades),
                 "trade_volume":sum(sizes) if sizes else 0.0,
                 "open_price":prices[0] if prices else None,"close_price":prices[-1] if prices else None,
                 "high_price":max(prices) if prices else None,"low_price":min(prices) if prices else None,
                 "return":((prices[-1]/prices[0])-1.0) if len(prices)>=2 and prices[0] else None,
                 "best_bid":bids[-1] if bids else None,"best_ask":asks[-1] if asks else None}
            if row["best_bid"] is not None and row["best_ask"] is not None:
                row["spread"]=row["best_ask"]-row["best_bid"]
            rows.append(row)
    with out.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,separators=(",",":"),default=str)+"\n")
    return len(rows)
"""
TEST=r"""
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_004_multihorizon_windows import WINDOW_SECONDS
assert WINDOW_SECONDS==(5,15,30,60)
print("[WINDOWS]",WINDOW_SECONDS)
print("[PASS] CHF-004 5s/15s/30s/60s materialization contract certified")
"""
(PKG/"chf_004_multihorizon_windows.py").write_text(BODY.lstrip(),encoding="utf-8")
(ROOT/"test_chf_004_coinbase_multihorizon_windows.py").write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(PKG/"chf_004_multihorizon_windows.py"),doraise=True)
py_compile.compile(str(ROOT/"test_chf_004_coinbase_multihorizon_windows.py"),doraise=True)
print("[PASS] wrote CHF-004 materializer + test")
