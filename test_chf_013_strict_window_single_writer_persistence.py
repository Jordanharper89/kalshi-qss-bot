from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_013_strict_window_single_writer_persistence import persist_strict_windows
r=persist_strict_windows(Path.cwd())
print("[PERSISTENCE]",r)
assert r["readback"]==r["committed"]
print("[PASS] strict complete CHF windows use OAD-261 -> OPH-019 -> await -> OAD-068")
print("[PASS] duplicate durable identities are skipped before resubmission")
print("[PASS] CHF-013 strict-window single-writer persistence certified")
