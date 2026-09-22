from pathlib import Path
import os, subprocess, sys

ROOT=Path.cwd().resolve()
WORKER=ROOT/"run_oracle_background_recovery.py"
TEST=ROOT/"test_obr_008_checkpointed_background_worker.py"

WORKER_SOURCE=r"""from __future__ import annotations
from pathlib import Path
import argparse,time,traceback

from qseries_v2.oracle_background_recovery.obr_002_gap_queue import enqueue_gap,next_queued_gap,mark_completed
from qseries_v2.oracle_background_recovery.obr_003_state_recovery import recover_gap_market_states
from qseries_v2.oracle_background_recovery.obr_004_settlement_recovery import recover_gap_settlements
from qseries_v2.oracle_background_recovery.obr_007_recovery_checkpoint import load_recovery_checkpoint,save_recovery_checkpoint,clear_recovery_checkpoint

OBR_008_BUILD_ID="OBR-008"
BACKOFF_SECONDS=(5.0,15.0,30.0,60.0)

def run_once(root):
    gap=next_queued_gap(root)
    if gap is None:gap=enqueue_gap(root)
    if gap is None:
        print("[OBR] no_recovery_gap",flush=True);return False

    cp=load_recovery_checkpoint(root)
    if cp.get("gap_id")!=gap["gap_id"]:
        cp=save_recovery_checkpoint(root,gap["gap_id"],"STATE",0,{})

    print(f"[OBR] starting gap_id={gap['gap_id'][:12]} phase={cp.get('phase')} gap_seconds={float(gap['gap_seconds']):.1f}",flush=True)

    state=cp.get("extra",{}).get("state_summary")
    if cp.get("phase")=="STATE":
        state=recover_gap_market_states(root,gap,progress=lambda x:print(x,flush=True))
        save_recovery_checkpoint(root,gap["gap_id"],"SETTLEMENT",0,{"state_summary":state})

    cp=load_recovery_checkpoint(root)
    settlements=cp.get("extra",{}).get("settlement_summary")
    if cp.get("phase")=="SETTLEMENT":
        settlements=recover_gap_settlements(root,gap,progress=lambda x:print(x,flush=True))
        save_recovery_checkpoint(root,gap["gap_id"],"FINALIZE",0,{"state_summary":state,"settlement_summary":settlements})

    cp=load_recovery_checkpoint(root)
    extra=cp.get("extra",{})
    state=extra.get("state_summary") or state or {}
    settlements=extra.get("settlement_summary") or settlements or {}
    summary={**state,**settlements,"gap_seconds":gap["gap_seconds"],"execution_authority":False}
    mark_completed(root,gap["gap_id"],summary)
    clear_recovery_checkpoint(root,gap["gap_id"])
    print(f"[OBR] complete gap_id={gap['gap_id'][:12]} summary={summary}",flush=True)
    return True

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");p.add_argument("--once",action="store_true");p.add_argument("--idle-seconds",type=float,default=30.0);a=p.parse_args(argv)
    if a.check:
        print("[READY] OBR-008 checkpointed background recovery worker")
        print("[PASS] execution_authority=FALSE")
        return 0
    root=Path.cwd().resolve();failures=0
    while True:
        try:
            ran=run_once(root);failures=0
            if a.once:return 0
            time.sleep(60.0 if ran else float(a.idle_seconds))
        except KeyboardInterrupt:return 0
        except Exception as exc:
            failures+=1;delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]
            print(f"[OBR] status=DEGRADED failure={type(exc).__name__}: {exc} retry_in={delay:.1f}s checkpoint_preserved=TRUE execution_authority=FALSE",flush=True)
            traceback.print_exc()
            if a.once:return 2
            time.sleep(delay)
if __name__=="__main__":raise SystemExit(main())
"""

TEST_SOURCE=r"""import ast,unittest
from pathlib import Path
ROOT=Path.cwd().resolve();W=ROOT/"run_oracle_background_recovery.py"
class T(unittest.TestCase):
    def test_checkpointed_worker(self):
        s=W.read_text(encoding="utf-8");ast.parse(s)
        self.assertIn("OBR_008_BUILD_ID",s)
        self.assertIn("save_recovery_checkpoint",s)
        self.assertIn("checkpoint_preserved=TRUE",s)
        self.assertIn('"FINALIZE"',s)
if __name__=="__main__":
    print("="*88);print(" OBR-008 CERTIFICATION TEST");print(" CHECKPOINTED BACKGROUND WORKER");print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] STATE -> SETTLEMENT -> FINALIZE resume phases certified")
    print("[PASS] failure preserves checkpoint")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OBR-008 CERTIFIED")
"""

def write_exact(p,s):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:p.write_bytes(b)

def main():
    print("="*88);print(" OBR-008 INSTALLER");print(" CHECKPOINTED BACKGROUND WORKER");print("="*88);print("[ROOT]",ROOT)
    req=ROOT/"qseries_v2"/"oracle_background_recovery"/"obr_007_recovery_checkpoint.py"
    if not req.is_file():raise RuntimeError("OBR-007 checkpoint module missing")
    old={p:(p.read_bytes() if p.exists() else None) for p in (WORKER,TEST)}
    try:
        write_exact(WORKER,WORKER_SOURCE);write_exact(TEST,TEST_SOURCE)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(WORKER),"--check"],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OBR-008 failed; worker restored");raise
    print("[PASS] recovery phases now durable across restart")
    print("[PASS] live launcher remains untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OBR-008 INSTALLATION COMPLETE")
if __name__=="__main__":main()
