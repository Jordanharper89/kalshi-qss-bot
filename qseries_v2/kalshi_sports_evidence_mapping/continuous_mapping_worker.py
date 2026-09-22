from pathlib import Path
from datetime import datetime,timezone
import json,time
from qseries_v2.kalshi_sports_evidence_mapping.durable_full_accounting_mapping_cycle import run_full_cycle

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

def _utc():
    return datetime.now(timezone.utc).isoformat()

def run_worker_cycle(root=None,universe_limit=1000,max_supported=40,timeout_seconds=15):
    root=Path(root or Path.cwd()).resolve()
    started=_utc()
    state=run_full_cycle(root=root,universe_limit=universe_limit,max_supported=max_supported,timeout_seconds=timeout_seconds)
    result={
        "schema_version":"KSEM-071","started_at":started,"completed_at":_utc(),
        "content_hash":state["content_hash"],"total_rows":state["total_rows"],
        "counts":state["counts"],"accounted_rows":state["accounted_rows"],
        "probability_enabled":False,"execution_authority":False,
    }
    path=root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_worker_heartbeat.json"
    path.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    return result

def run_forever(root=None,interval_seconds=60,stop_after_cycles=None):
    cycles=0
    while True:
        run_worker_cycle(root=root)
        cycles+=1
        if stop_after_cycles is not None and cycles>=int(stop_after_cycles):
            return cycles
        time.sleep(max(1,int(interval_seconds)))
