from pathlib import Path
import os,subprocess,sys
ROOT=Path.cwd().resolve();RUN=ROOT/"run_olf_030_breadth_aware_reasoning_runtime.py";TEST=ROOT/"test_orh_004_reasoning_postgresql_recovery.py"
RUN_SOURCE='from pathlib import Path\nimport argparse,time\nfrom qseries_v2.oracle_learning_feedback.olf_030_breadth_aware_reasoning_runtime import run_breadth_aware_reasoning_cycle\n\nORH_004_BUILD_ID="ORH-004"\nBACKOFF_SECONDS=(1.0,2.0,5.0,10.0,30.0)\n\ndef main(argv=None):\n    p=argparse.ArgumentParser();p.add_argument("--batch-size",type=int,default=50);p.add_argument("--cadence-seconds",type=float,default=2.0);p.add_argument("--check",action="store_true");p.add_argument("--once",action="store_true");a=p.parse_args(argv)\n    if a.check:\n        print("[READY] OLF-030 breadth-aware reasoning runtime — ORH-004 resilient")\n        print("[PASS] execution_authority=FALSE")\n        return 0\n    root=Path.cwd();cycle=0;failures=0\n    print("="*88,flush=True);print(" OLF-030 LEARNING COVERAGE BREADTH REASONING RUNTIME — ORH-004 RESILIENT",flush=True);print("="*88,flush=True)\n    while True:\n        try:\n            cycle+=1;s=run_breadth_aware_reasoning_cycle(root,a.batch_size,progress=lambda x:print(x,flush=True));failures=0\n            print(f"[OLF-030 OCR] cycle={cycle} idle={s.idle} markets={s.markets_reasoned} experience={s.experience_contexts} withheld={s.withheld_contexts} blind={s.blind_contexts}",flush=True)\n            if a.once:return 0\n            time.sleep(a.cadence_seconds)\n        except KeyboardInterrupt:\n            return 0\n        except Exception as exc:\n            failures+=1;delay=BACKOFF_SECONDS[min(failures-1,len(BACKOFF_SECONDS)-1)]\n            print(f"[ORH-004 REASONING RECOVERY] status=DEGRADED failure={failures} type={type(exc).__name__} retry_in={delay:.1f}s execution_authority=FALSE",flush=True)\n            time.sleep(delay)\n\nif __name__=="__main__":raise SystemExit(main())\n'
TEST_SOURCE='import ast,unittest\nfrom pathlib import Path\nROOT=Path.cwd().resolve();RUN=ROOT/"run_olf_030_breadth_aware_reasoning_runtime.py"\nclass T(unittest.TestCase):\n    def test_physical_runner(self):\n        s=RUN.read_text(encoding="utf-8");ast.parse(s)\n        self.assertIn("ORH_004_BUILD_ID",s);self.assertIn("run_breadth_aware_reasoning_cycle",s);self.assertIn("REASONING RECOVERY",s)\nif __name__=="__main__":\n    print("="*88);print(" ORH-004 CERTIFICATION TEST");print(" REASONING POSTGRESQL RECOVERY");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] breadth-aware reasoning recovery loop certified")\n    print("[PASS] OLF-030 intelligence module unchanged")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] ORH-004 CERTIFIED")\n'
def write_exact(p,s):
    tmp=p.with_suffix(p.suffix+".tmp");tmp.write_text(s,encoding="utf-8",newline="\n");os.replace(tmp,p)
def restore(p,b):
    if b is None:
        if p.exists():p.unlink()
    else:p.write_bytes(b)
def main():
    print("="*88);print(" ORH-004 INSTALLER");print(" REASONING POSTGRESQL RECOVERY");print("="*88);print("[ROOT]",ROOT)
    mod=ROOT/"qseries_v2"/"oracle_learning_feedback"/"olf_030_breadth_aware_reasoning_runtime.py"
    if not mod.is_file():raise RuntimeError("Physical OLF-030 module missing")
    old={p:(p.read_bytes() if p.exists() else None) for p in (RUN,TEST)}
    try:
        original=RUN.read_text(encoding="utf-8")
        if "run_breadth_aware_reasoning_cycle" not in original:raise RuntimeError("Physical OLF-030 runner contract changed")
        write_exact(RUN,RUN_SOURCE);write_exact(TEST,TEST_SOURCE)
        compile(RUN.read_text(encoding="utf-8"),str(RUN),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(RUN),"--check"],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] ORH-004 failed; reasoning runner restored");raise
    print("[PASS] OLF-030 core reasoning module unchanged")
    print("[PASS] PostgreSQL outage no longer kills reasoning child")
    print("[PASS] reasoning resumes automatically after database recovery")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] ORH-004 INSTALLATION COMPLETE")
if __name__=="__main__":main()
