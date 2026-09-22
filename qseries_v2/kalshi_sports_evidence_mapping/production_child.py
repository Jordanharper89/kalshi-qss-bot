from pathlib import Path
import os
from qseries_v2.kalshi_sports_evidence_mapping.restart_checkpoint_recovery import recover_and_resume
from qseries_v2.kalshi_sports_evidence_mapping.continuous_mapping_worker import run_forever

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def run(root=None,interval_seconds=None,stop_after_cycles=None):
    root=Path(root or Path.cwd()).resolve()
    recover_and_resume(root)
    interval=int(interval_seconds if interval_seconds is not None else os.environ.get("KSEM_INTERVAL_SECONDS","60"))
    return run_forever(root=root,interval_seconds=interval,stop_after_cycles=stop_after_cycles)
