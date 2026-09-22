from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_022_supervisor_restart_gap_lineage import record_supervisor_restart
r,p=record_supervisor_restart(Path.cwd(),"RUNNING","RESTARTED")
assert r["gap_policy"]=="DETECT_AND_MARK;NO_SYNTHETIC_BACKFILL"
assert r["execution_authority"] is False
assert p.exists()
print("[PASS] supervisor restart lineage recorded")
print("[PASS] synthetic backfill prohibited")
print("[PASS] CHF-022 restart/gap lineage certified")
