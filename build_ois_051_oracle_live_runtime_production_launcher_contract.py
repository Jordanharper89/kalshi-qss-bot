from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_051_runtime_launcher_contract.py"
TEST = ROOT / "test_ois_051_oracle_live_runtime_production_launcher_contract.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_051_BUILD_ID="OIS-051"\nOIS_051_REVISION="OIS_051_ORACLE_LIVE_RUNTIME_PRODUCTION_LAUNCHER_CONTRACT_V1"\n\n@dataclass(frozen=True)\nclass OracleRuntimeLaunchContract:\n    launcher_name:str\n    runtime_name:str\n    terminal_dependency:bool\n    requires_certified_dependencies:bool\n    execution_authority:bool\n    continuous:bool\n\ndef build_oracle_runtime_launch_contract(launcher_name="run_oracle_LIVE.py"):\n    if not launcher_name:\n        raise ValueError("launcher_name required")\n    return OracleRuntimeLaunchContract(\n        launcher_name,\n        "Oracle Live Runtime",\n        False,\n        True,\n        False,\n        True,\n    )\n\ndef verify_ois_051_oracle_live_runtime_production_launcher_contract():\n    x=build_oracle_runtime_launch_contract()\n    return (\n        x.launcher_name=="run_oracle_LIVE.py"\n        and x.runtime_name=="Oracle Live Runtime"\n        and not x.terminal_dependency\n        and x.requires_certified_dependencies\n        and not x.execution_authority\n        and x.continuous\n    )\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_051_runtime_launcher_contract import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_051_oracle_live_runtime_production_launcher_contract())\n\n    def test_terminal_independent(self):\n        self.assertFalse(build_oracle_runtime_launch_contract().terminal_dependency)\n\n    def test_no_execution(self):\n        self.assertFalse(build_oracle_runtime_launch_contract().execution_authority)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-051 CERTIFICATION TEST");print(" ORACLE LIVE RUNTIME PRODUCTION LAUNCHER CONTRACT");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle Live Runtime production launcher contract certified")\n    print("[DONE] OIS-051 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_050_runtime_activation_gate")
    if getattr(upstream, "verify_ois_050_oracle_live_runtime_activation_capability_gate")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_051_runtime_launcher_contract import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-051 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-051 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
