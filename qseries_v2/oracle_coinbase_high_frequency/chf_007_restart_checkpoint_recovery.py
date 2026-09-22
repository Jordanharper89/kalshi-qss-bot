import json
from pathlib import Path
from .chf_001_foundation import runtime_dir
from .chf_006_continuous_multihorizon_worker import ContinuousWindowWorker

REVISION="CHF-007"

def certify_restart(root:Path):
    root=Path(root)
    d=runtime_dir(root)
    raw=d/"raw_events.jsonl"
    cp=d/"continuous_window_checkpoint.json"
    if not raw.exists():
        raise RuntimeError("CHF-005 physical raw journal required")
    worker=ContinuousWindowWorker(root)
    first=worker.cycle()
    before=json.loads(cp.read_text(encoding="utf-8"))["raw_offset"]
    second=worker.cycle()
    after=json.loads(cp.read_text(encoding="utf-8"))["raw_offset"]
    if after!=before:
        raise AssertionError("checkpoint moved without new raw input")
    if second["raw_lines"]!=0:
        raise AssertionError("restart replayed already-consumed raw rows")
    if before>raw.stat().st_size:
        raise AssertionError("checkpoint beyond raw journal")
    return {
        "first":first,
        "second":second,
        "checkpoint":before,
        "raw_size":raw.stat().st_size,
    }
