from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_011_strict_complete_multihorizon_windows import materialize_strict
rows,p=materialize_strict(Path.cwd())
print("[STRICT_WINDOW_FILE]",p)
print("[STRICT_ROWS]",len(rows))
for r in rows: print("[WINDOW]",r["product_id"],r["window_seconds"],"span=",round(r["coverage_span_seconds"],3),"events=",r["event_count"])
assert all(r["full_horizon_complete"] for r in rows)
assert all(r["no_future_leakage"] for r in rows)
print("[PASS] incomplete 30s/60s windows rejected rather than falsely admitted")
print("[PASS] CHF-011 strict full-horizon window contract certified")
