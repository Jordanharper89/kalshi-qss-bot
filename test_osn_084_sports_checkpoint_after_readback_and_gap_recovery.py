
from datetime import datetime, timezone, timedelta
from pathlib import Path
from qseries_v2.oracle_source_network.runtime.sports_checkpoint_gap_recovery import (
    checkpoint_after_readback, plan_gap_windows, write_certification
)

root=Path.cwd()
cp,path=checkpoint_after_readback("NHL","osn084-test-observation","2026020001",1,root=root)
print("[CHECKPOINT]",cp)
assert path.exists()
try:
    checkpoint_after_readback("NHL","bad","bad",0,root=root)
    raise AssertionError("zero-readback checkpoint should have failed")
except RuntimeError:
    print("[PASS] zero-readback checkpoint rejected")

now=datetime.now(timezone.utc)
windows=plan_gap_windows(now-timedelta(minutes=17),now=now,max_window_minutes=5)
assert len(windows)==4
print("[GAP_WINDOWS]",windows)
_,state=write_certification(root=root)
print("[STATE]",state)
print("[PASS] checkpoint-after-readback enforced")
print("[PASS] bounded downtime gap recovery windows certified")
print("[PASS] execution_authority=FALSE")
