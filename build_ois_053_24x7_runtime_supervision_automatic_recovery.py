from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_053_runtime_supervision.py"
TEST = ROOT / "test_ois_053_24x7_runtime_supervision_automatic_recovery.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_046_runtime_state import OracleLiveRuntimeState\nfrom .ois_047_runtime_activation import transition_runtime\n\nOIS_053_BUILD_ID="OIS-053"\nOIS_053_REVISION="OIS_053_24X7_RUNTIME_SUPERVISION_AUTOMATIC_RECOVERY_V1"\n\n@dataclass(frozen=True)\nclass RuntimeSupervisionDecision:\n    action:str\n    next_state:str\n    restart_required:bool\n    reason:str\n\ndef supervise_runtime(runtime_state,aggregate_healthy,recovery_ready):\n    if not isinstance(runtime_state,OracleLiveRuntimeState):\n        raise ValueError("certified runtime state required")\n\n    if runtime_state.state=="STOPPED":\n        return RuntimeSupervisionDecision("HOLD","STOPPED",False,"stopped")\n\n    if aggregate_healthy:\n        if runtime_state.state in ("DEGRADED","RECOVERING","STARTING"):\n            return RuntimeSupervisionDecision("PROMOTE_RUNNING","RUNNING",False,"healthy")\n        return RuntimeSupervisionDecision("CONTINUE","RUNNING",False,"healthy")\n\n    if recovery_ready:\n        return RuntimeSupervisionDecision("ENTER_RECOVERY","RECOVERING",False,"degraded_recoverable")\n\n    return RuntimeSupervisionDecision("RESTART","DEGRADED",True,"recovery_not_ready")\n\ndef apply_supervision_decision(runtime_state,decision):\n    if decision.next_state==runtime_state.state:\n        return runtime_state\n    accepting=decision.next_state=="RUNNING"\n    serving=decision.next_state in ("RUNNING","DEGRADED","RECOVERING")\n    return transition_runtime(runtime_state,decision.next_state,accepting,serving)\n\ndef verify_ois_053_24x7_runtime_supervision_automatic_recovery():\n    from .ois_046_runtime_state import build_oracle_live_runtime_state\n    r=build_oracle_live_runtime_state("RUNNING",5,True,True)\n    d=supervise_runtime(r,False,True)\n    x=apply_supervision_decision(r,d)\n    return d.action=="ENTER_RECOVERY" and x.state=="RECOVERING" and not d.restart_required\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_046_runtime_state import build_oracle_live_runtime_state\nfrom qseries_v2.oracle_intelligence_state.ois_053_runtime_supervision import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_053_24x7_runtime_supervision_automatic_recovery())\n\n    def test_restart_when_unrecoverable(self):\n        r=build_oracle_live_runtime_state("RUNNING",1,True,True)\n        self.assertTrue(supervise_runtime(r,False,False).restart_required)\n\n    def test_healthy_continues(self):\n        r=build_oracle_live_runtime_state("RUNNING",1,True,True)\n        self.assertEqual(supervise_runtime(r,True,True).action,"CONTINUE")\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-053 CERTIFICATION TEST");print(" 24/7 RUNTIME SUPERVISION + AUTOMATIC RECOVERY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle 24/7 runtime supervision/recovery coordination certified")\n    print("[DONE] OIS-053 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_052_startup_readiness")
    if getattr(upstream, "verify_ois_052_runtime_startup_dependency_readiness_gate")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_053_runtime_supervision import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-053 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-053 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
