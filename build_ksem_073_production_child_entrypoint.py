from pathlib import Path
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"; STATE=PKG/"state"
MOD=PKG/"production_child.py"; RUNNER=ROOT/"run_ksem_live_mapping.py"; TEST=ROOT/"test_ksem_073_production_child_entrypoint.py"
MODULE=r"""
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
"""
RUNNER_BODY=r"""
from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.production_child import run
if __name__=="__main__":
    run(Path.cwd())
"""
TEST_BODY=r"""
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
"""
def main():
    print("="*120); print(" KSEM-073 PRODUCTION CHILD ENTRYPOINT INSTALLER"); print("="*120)
    if not (PKG/"restart_checkpoint_recovery.py").is_file(): raise RuntimeError("KSEM-072 dependency missing")
    MOD.write_text(MODULE.lstrip(),encoding="utf-8"); RUNNER.write_text(RUNNER_BODY.lstrip(),encoding="utf-8"); TEST.write_text(TEST_BODY.lstrip(),encoding="utf-8")
    print("[PASS] wrote",MOD.relative_to(ROOT)); print("[PASS] wrote",RUNNER.name); print("[PASS] wrote",TEST.name)
    print("[PASS] standalone child created without mutating run_oracle_LIVE.py")
    print("[PASS] KSEM-073 installer complete")
if __name__=="__main__": main()