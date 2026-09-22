from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_023_runtime_recovery.py"
TEST = ROOT / "test_ois_023_runtime_checkpoint_crash_recovery_coordination.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_023_BUILD_ID="OIS-023"\nOIS_023_REVISION="OIS_023_RUNTIME_CHECKPOINT_CRASH_RECOVERY_COORDINATION_V1"\n\n@dataclass(frozen=True)\nclass RuntimeRecoveryState:\n    cycle_sequence:int\n    intake_sequence:int\n    state_version:int\n    recovery_ready:bool\n\ndef coordinate_runtime_recovery(cycle_sequence,intake_sequence,state_version):\n    vals=(int(cycle_sequence),int(intake_sequence),int(state_version))\n    if any(x<0 for x in vals): raise ValueError("non-negative recovery coordinates required")\n    ready = vals[0]>=0 and vals[1]>=0 and vals[2]>=0\n    return RuntimeRecoveryState(*vals,ready)\n\ndef next_safe_cycle(recovery):\n    if not recovery.recovery_ready: raise ValueError("runtime recovery not ready")\n    return recovery.cycle_sequence+1\n\ndef verify_ois_023_runtime_checkpoint_crash_recovery_coordination():\n    r=coordinate_runtime_recovery(10,25,7)\n    return r.recovery_ready and next_safe_cycle(r)==11\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_023_runtime_recovery import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ois_023_runtime_checkpoint_crash_recovery_coordination())\n    def test_next_cycle(self): self.assertEqual(next_safe_cycle(coordinate_runtime_recovery(5,9,2)),6)\n    def test_negative(self):\n        with self.assertRaises(ValueError): coordinate_runtime_recovery(-1,0,0)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-023 CERTIFICATION TEST");print(" RUNTIME CHECKPOINT + CRASH RECOVERY COORDINATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Unified runtime checkpoint/crash-recovery coordination certified")\n    print("[DONE] OIS-023 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_022_pipeline_orchestrator")
    if getattr(upstream, "verify_ois_022_continuous_pipeline_cycle_orchestrator")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_023_runtime_recovery import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-023 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-023 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
