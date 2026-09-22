from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_024_service_activation.py"
TEST = ROOT / "test_ois_024_24x7_service_activation_health_boundary.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_024_BUILD_ID="OIS-024"\nOIS_024_REVISION="OIS_024_24X7_SERVICE_ACTIVATION_HEALTH_BOUNDARY_V1"\n\n@dataclass(frozen=True)\nclass OracleServiceState:\n    active:bool\n    healthy:bool\n    lag_seconds:float\n    restart_required:bool\n    terminal_dependency:bool=False\n\ndef evaluate_oracle_service(active,db_ok,pipeline_ok,recovery_ok,lag_seconds,max_lag_seconds=30.0):\n    lag=float(lag_seconds)\n    if lag<0: raise ValueError("lag must be non-negative")\n    healthy=bool(active and db_ok and pipeline_ok and recovery_ok and lag<=max_lag_seconds)\n    restart=bool(active and (not db_ok or not pipeline_ok or not recovery_ok))\n    return OracleServiceState(bool(active),healthy,lag,restart,False)\n\ndef verify_ois_024_24x7_service_activation_health_boundary():\n    h=evaluate_oracle_service(True,True,True,True,1.0)\n    d=evaluate_oracle_service(True,False,True,True,1.0)\n    return h.healthy and not h.terminal_dependency and d.restart_required\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_024_service_activation import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ois_024_24x7_service_activation_health_boundary())\n    def test_lag_unhealthy(self): self.assertFalse(evaluate_oracle_service(True,True,True,True,31).healthy)\n    def test_terminal_independent(self): self.assertFalse(evaluate_oracle_service(True,True,True,True,1).terminal_dependency)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-024 CERTIFICATION TEST");print(" 24/7 SERVICE ACTIVATION + HEALTH BOUNDARY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] 24/7 Oracle service activation/health boundary certified")\n    print("[DONE] OIS-024 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_023_runtime_recovery")
    if getattr(upstream, "verify_ois_023_runtime_checkpoint_crash_recovery_coordination")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_024_service_activation import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-024 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-024 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
