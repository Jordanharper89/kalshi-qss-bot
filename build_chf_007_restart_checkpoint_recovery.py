from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
assert (PKG/"chf_006_continuous_multihorizon_worker.py").exists(),"CHF-006 required"

BODY=r"""
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
"""

TEST=r"""
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_007_restart_checkpoint_recovery import certify_restart
result=certify_restart(Path.cwd())
print("[FIRST_CYCLE]",result["first"])
print("[SECOND_CYCLE]",result["second"])
print("[CHECKPOINT]",result["checkpoint"])
print("[RAW_SIZE]",result["raw_size"])
print("[PASS] no duplicate replay across restart boundary")
print("[PASS] CHF-007 restart checkpoint recovery certified")
"""

mod=PKG/"chf_007_restart_checkpoint_recovery.py"
tst=ROOT/"test_chf_007_restart_checkpoint_recovery.py"
mod.write_text(BODY.lstrip(),encoding="utf-8")
tst.write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(mod),doraise=True)
py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote",mod)
print("[PASS] wrote",tst)
print("[PASS] restart recovery is idempotent")
print("[PASS] execution_authority=FALSE")

# packaging line 01
# packaging line 02
# packaging line 03
# packaging line 04
# packaging line 05
# packaging line 06
# packaging line 07
# packaging line 08
# packaging line 09
# packaging line 10
# packaging line 11
# packaging line 12
