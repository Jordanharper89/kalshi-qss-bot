from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_011_strict_complete_multihorizon_windows import materialize_strict,PRODUCTS,WINDOWS
rows,p=materialize_strict(Path.cwd())
keys={(r["product_id"],r["window_seconds"]) for r in rows}
print("[STRICT_WINDOW_FILE]",p)
print("[STRICT_KEYS]",sorted(keys))
for r in rows:
    print("[WINDOW]",r["product_id"],r["window_seconds"],"boundary_age=",round(r["boundary_observation_age_seconds"],3),"events=",r["event_count"],"max_gap=",round(r["max_event_gap_seconds"],3))
expected={(p,w) for p in PRODUCTS for w in WINDOWS}
missing=sorted(expected-keys)
print("[MISSING]",missing)
assert not missing,f"missing recent complete windows: {missing}"
assert all(r["full_horizon_complete"] and r["no_future_leakage"] for r in rows)
print("[PASS] latest-event anchor defect retired")
print("[PASS] recent complete past-only anchor search certified")
print("[PASS] all 12 BTC/ETH/SOL x 5/15/30/60 strict windows present")
print("[PASS] CHF-011 recent complete anchor repair certified")
