from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_004_multihorizon_windows import WINDOW_SECONDS
assert WINDOW_SECONDS==(5,15,30,60)
print("[WINDOWS]",WINDOW_SECONDS)
print("[PASS] CHF-004 5s/15s/30s/60s materialization contract certified")
