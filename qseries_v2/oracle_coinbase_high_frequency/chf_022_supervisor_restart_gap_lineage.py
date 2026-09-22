from pathlib import Path
import json
from datetime import datetime, timezone

def record_supervisor_restart(root, prior_state, current_state):
    root=Path(root)
    p=root/"runtime"/"coinbase_hf"/"supervisor_gap_lineage.jsonl"
    p.parent.mkdir(parents=True,exist_ok=True)
    rec={
      "schema_version":"CHF-022",
      "recorded_at":datetime.now(timezone.utc).isoformat(),
      "event":"ORACLE_SUPERVISOR_CHILD_RESTART",
      "prior_state":prior_state,
      "current_state":current_state,
      "gap_policy":"DETECT_AND_MARK;NO_SYNTHETIC_BACKFILL",
      "execution_authority":False,
    }
    with p.open("a",encoding="utf-8") as f:
        f.write(json.dumps(rec,sort_keys=True)+"\n")
    return rec,p
