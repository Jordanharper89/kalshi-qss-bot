from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.production_child import run,READ_ONLY,EXECUTION_AUTHORITY,PROBABILITY_ENABLED
root=Path.cwd()
cycles=run(root=root,interval_seconds=1,stop_after_cycles=1)
print("[CYCLES]",cycles)
assert cycles==1
assert READ_ONLY is True and EXECUTION_AUTHORITY is False and PROBABILITY_ENABLED is False
assert (root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_worker_heartbeat.json").is_file()
print("[PASS] standalone KSEM production child entrypoint completed bounded physical cycle")
print("[PASS] KSEM-073 certified")
