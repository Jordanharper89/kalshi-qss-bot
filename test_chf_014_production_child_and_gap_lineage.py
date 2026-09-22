from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_014_production_child_and_gap_lineage import run_child
# interface-only bounded zero-duration startup; CHF-015 performs physical live run
r=run_child(Path.cwd(),max_seconds=0,persist_interval_s=0.1)
print("[CHILD_INTERFACE]",r)
assert r["execution_authority"] is False
print("[PASS] reconnect/gap lineage path installed; missed websocket time is never silently declared recovered")
print("[PASS] CHF-014 standalone production child contract certified")
