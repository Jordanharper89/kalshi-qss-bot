import json
import statistics
import threading
import time
from datetime import datetime
from pathlib import Path

from qseries_v2.oracle_coinbase_high_frequency.chf_014_production_child_and_gap_lineage import run_child
from qseries_v2.oracle_coinbase_high_frequency.chf_011_strict_complete_multihorizon_windows import materialize_strict
from qseries_v2.oracle_coinbase_high_frequency.chf_013_strict_window_single_writer_persistence import persist_strict_windows

ROOT=Path.cwd()
D=ROOT/"runtime"/"coinbase_hf"
PRODUCTS=("BTC-USD","ETH-USD","SOL-USD")
WINDOWS=(5,15,30,60)
EXPECTED={(p,w) for p in PRODUCTS for w in WINDOWS}

for name in (
    "raw_events.jsonl",
    "canonical_events.jsonl",
    "strict_condition_windows.jsonl",
    "continuous_window_checkpoint.json",
    "worker_state.json",
):
    p=D/name
    if p.exists():
        p.unlink()

result_box={}
error_box={}

def child():
    try:
        result_box["result"]=run_child(
            ROOT,
            max_seconds=125,
            persist_interval_s=5.0,
        )
    except Exception as e:
        error_box["error"]=e

print("[PHYSICAL] starting readiness-driven Coinbase HF acquisition")
t=threading.Thread(target=child,daemon=True)
t.start()

deadline=time.monotonic()+120.0
last_missing=None
ready=False

while time.monotonic()<deadline:
    time.sleep(2.0)
    try:
        rows,_=materialize_strict(ROOT)
    except Exception:
        continue

    keys={(r["product_id"],r["window_seconds"]) for r in rows}
    missing=sorted(EXPECTED-keys)

    if missing!=last_missing:
        print("[READINESS] present=",len(keys),"missing=",missing)
        last_missing=missing

    if not missing:
        ready=True
        break

if not ready:
    rows,_=materialize_strict(ROOT)
    keys={(r["product_id"],r["window_seconds"]) for r in rows}
    spans={}
    canonical=D/"canonical_events.jsonl"

    if canonical.exists():
        per={p:[] for p in PRODUCTS}
        for line in canonical.read_text(encoding="utf-8").splitlines():
            try:
                r=json.loads(line)
            except Exception:
                continue

            payload=r.get("payload") if isinstance(r.get("payload"),dict) else {}
            product=r.get("product_id") or payload.get("product_id")
            if product not in per:
                continue

            value=(
                r.get("observed_at")
                or r.get("event_time")
                or r.get("timestamp")
                or r.get("time")
                or r.get("received_at")
                or payload.get("observed_at")
                or payload.get("event_time")
                or payload.get("timestamp")
                or payload.get("time")
            )
            if not value:
                continue

            try:
                s=str(value)
                if s.endswith("Z"):
                    s=s[:-1]+"+00:00"
                per[product].append(datetime.fromisoformat(s).timestamp())
            except Exception:
                pass

        for product,ts in per.items():
            spans[product]=round(max(ts)-min(ts),3) if len(ts)>=2 else 0.0

    raise AssertionError(
        f"CHF-015 readiness timeout | missing={sorted(EXPECTED-keys)} | event_time_spans={spans}"
    )

print("[READINESS] all 12 strict windows physically present")

persist=persist_strict_windows(ROOT)
print("[PERSISTENCE]",persist)
assert persist["readback"]==persist["committed"]

raw=D/"raw_events.jsonl"
raw_lines=raw.read_text(encoding="utf-8").splitlines()
times=[]

for line in raw_lines:
    try:
        r=json.loads(line)
        v=r.get("received_at") or r.get("acquired_at")
        if not v:
            continue
        s=str(v)
        if s.endswith("Z"):
            s=s[:-1]+"+00:00"
        times.append(datetime.fromisoformat(s).timestamp())
    except Exception:
        pass

gaps=[b-a for a,b in zip(times,times[1:]) if b>=a]
median_gap=statistics.median(gaps) if gaps else None

rows,_=materialize_strict(ROOT)
keys={(r["product_id"],r["window_seconds"]) for r in rows}

print("[RAW_MESSAGES]",len(raw_lines))
print("[STRICT_WINDOWS]",len(rows))
print("[STRICT_KEYS]",sorted(keys))
print("[RAW_MEDIAN_RECEIVE_GAP_S]",median_gap)

assert EXPECTED.issubset(keys)
assert len(raw_lines)>0

print("[PROBABILITY_ENABLED]",False)
print("[DIRECTION_ENABLED]",False)
print("[PUBLICATION_ALLOWED]",False)
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] fixed-duration 66-second CHF-015 gate retired")
print("[PASS] readiness-driven full-horizon acquisition certified")
print("[PASS] all BTC/ETH/SOL x 5/15/30/60 windows physically complete")
print("[PASS] strict windows persisted through exact single-writer lifecycle")
print("[PASS] CHF-015 physical production-capability certification complete")
