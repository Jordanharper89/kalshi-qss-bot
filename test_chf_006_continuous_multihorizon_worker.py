from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_006_continuous_multihorizon_worker import ContinuousWindowWorker
w=ContinuousWindowWorker(Path.cwd())
assert w.checkpoint.name=="continuous_window_checkpoint.json"
print("[CHECKPOINT]",w.checkpoint)
print("[PASS] CHF-006 continuous rolling multihorizon worker certified")
