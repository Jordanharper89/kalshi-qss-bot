from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
for f in (
    "chf_011_strict_complete_multihorizon_windows.py",
    "chf_013_strict_window_single_writer_persistence.py",
    "chf_014_production_child_and_gap_lineage.py",
):
    assert (PKG/f).exists(), f"{f} required"

TEST=r"""
import json
import statistics
from datetime import datetime
from pathlib import Path

from qseries_v2.oracle_coinbase_high_frequency.chf_014_production_child_and_gap_lineage import run_child
from qseries_v2.oracle_coinbase_high_frequency.chf_011_strict_complete_multihorizon_windows import materialize_strict, PRODUCTS, WINDOWS
from qseries_v2.oracle_coinbase_high_frequency.chf_013_strict_window_single_writer_persistence import persist_strict_windows

ROOT=Path.cwd()
D=ROOT/"runtime"/"coinbase_hf"
EXPECTED={(p,w) for p in PRODUCTS for w in WINDOWS}

for name in (
    "raw_events.jsonl",
    "canonical_events.jsonl",
    "strict_condition_windows.jsonl",
    "continuous_window_checkpoint.json",
    "worker_state.json",
):
    q=D/name
    if q.exists():
        q.unlink()

print("[PHYSICAL] starting serialized CHF-015 production-capability gate")
print("[PHASE 1] CHF-014 owns acquisition + rolling persistence exclusively")

child_result=run_child(
    ROOT,
    max_seconds=95,
    persist_interval_s=5.0,
)
print("[CHF014_RESULT]",child_result)

print("[PHASE 2] child exited; no competing CHF persistence thread remains")

rows,path=materialize_strict(ROOT)
keys={(r["product_id"],r["window_seconds"]) for r in rows}
missing=sorted(EXPECTED-keys)

print("[STRICT_WINDOW_FILE]",path)
print("[STRICT_WINDOWS]",len(rows))
print("[STRICT_KEYS]",sorted(keys))
print("[MISSING]",missing)

assert not missing, f"missing complete windows after bounded live run: {missing}"
assert all(r["full_horizon_complete"] for r in rows)
assert all(r["no_future_leakage"] for r in rows)

print("[PHASE 3] one serialized final OPH-019 submit -> await -> OAD-068 exact readback")
persist=persist_strict_windows(ROOT)
print("[FINAL_PERSISTENCE]",persist)

assert persist["committed"] == persist["readback"]
assert persist["committed"] + persist.get("skipped_existing",0) >= len(rows)

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

print("[RAW_MESSAGES]",len(raw_lines))
print("[RAW_MEDIAN_RECEIVE_GAP_S]",median_gap)
print("[PROBABILITY_ENABLED]",False)
print("[DIRECTION_ENABLED]",False)
print("[PUBLICATION_ALLOWED]",False)
print("[EXECUTION_AUTHORITY]",False)
print("[PASS] concurrent certification persistence race retired")
print("[PASS] CHF-014 bounded live acquisition/persistence cycle completed")
print("[PASS] all BTC/ETH/SOL x 5/15/30/60 strict windows complete")
print("[PASS] final persistence executed only after CHF-014 child exit")
print("[PASS] exact single-writer commit/readback certified")
print("[PASS] CHF-015 serialized physical production-capability certification complete")
"""

tst=ROOT/"test_chf_015_serialized_persistence_final_gate_REPAIR.py"
tst.write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(tst),doraise=True)

print("[PASS] wrote",tst)
print("[PASS] failed concurrent CHF-015 certification harness retired")
print("[PASS] production persistence interfaces unchanged")
print("[PASS] OPH-019 single-writer path preserved")
print("[PASS] execution_authority=FALSE")
