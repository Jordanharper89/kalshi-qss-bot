import json,statistics,time
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_014_production_child_and_gap_lineage import run_child
from qseries_v2.oracle_coinbase_high_frequency.chf_011_strict_complete_multihorizon_windows import materialize_strict
from qseries_v2.oracle_coinbase_high_frequency.chf_013_strict_window_single_writer_persistence import persist_strict_windows

ROOT=Path.cwd()
D=ROOT/"runtime"/"coinbase_hf"
for name in ("raw_events.jsonl","canonical_events.jsonl","strict_condition_windows.jsonl","continuous_window_checkpoint.json","worker_state.json"):
    p=D/name
    if p.exists(): p.unlink()

print("[PHYSICAL] starting fresh public Coinbase HF acquisition for strict 60-second coverage")
result=run_child(ROOT,max_seconds=66,persist_interval_s=5.0)
rows,path=materialize_strict(ROOT)
counts={}
for r in rows:
    counts[(r["product_id"],r["window_seconds"])]=r
print("[STRICT_KEYS]",sorted(counts))
for product in ("BTC-USD","ETH-USD","SOL-USD"):
    for sec in (5,15,30,60):
        assert (product,sec) in counts,f"missing strict complete window {(product,sec)}"
        assert counts[(product,sec)]["coverage_span_seconds"] >= sec-0.25
        assert counts[(product,sec)]["full_horizon_complete"] is True

persist=persist_strict_windows(ROOT)
raw_lines=(D/"raw_events.jsonl").read_text(encoding="utf-8").splitlines()
times=[]
for line in raw_lines:
    try:
        x=json.loads(line)
        v=x.get("received_at") or x.get("acquired_at")
        if v:
            if str(v).endswith("Z"): v=str(v)[:-1]+"+00:00"
            from datetime import datetime
            times.append(datetime.fromisoformat(str(v)).timestamp())
    except Exception: pass
gaps=[b-a for a,b in zip(times,times[1:]) if b>=a]
median_gap=statistics.median(gaps) if gaps else None
print("[RAW_MESSAGES]",len(raw_lines))
print("[STRICT_WINDOWS]",len(rows))
print("[STRICT_60S]",sum(1 for r in rows if r["window_seconds"]==60))
print("[PERSISTENCE]",persist)
print("[RAW_MEDIAN_RECEIVE_GAP_S]",median_gap)
assert len(raw_lines)>0
assert len(rows)>=12
assert sum(1 for r in rows if r["window_seconds"]==60)==3
assert persist["readback"]==persist["committed"]
print("[PROBABILITY_ENABLED]",False)
print("[DIRECTION_ENABLED]",False)
print("[PUBLICATION_ALLOWED]",False)
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] fresh live Coinbase HF -> strict complete 5/15/30/60s -> PostgreSQL -> exact readback certified")
print("[PASS] CHF-015 physical production-capability certification complete")
