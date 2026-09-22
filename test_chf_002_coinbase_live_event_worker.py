from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_002_live_event_worker import CoinbaseHFWorker
w=CoinbaseHFWorker(Path.cwd())
assert w.raw.name=="raw_events.jsonl"
assert w.state.name=="worker_state.json"
print("[RAW_JOURNAL]",w.raw)
print("[STATE]",w.state)
print("[PASS] CHF-002 live event worker interface certified")
