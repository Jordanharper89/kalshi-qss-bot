from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_046_runtime_state.py"
TEST = ROOT / "test_ois_046_oracle_live_runtime_state_model.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\n\nOIS_046_BUILD_ID="OIS-046"\nOIS_046_REVISION="OIS_046_ORACLE_LIVE_RUNTIME_STATE_MODEL_V1"\n\nRUNTIME_STATES=("STARTING","RUNNING","DEGRADED","RECOVERING","STOPPED")\n\n@dataclass(frozen=True)\nclass OracleLiveRuntimeState:\n    state:str\n    sequence:int\n    active:bool\n    accepting_intelligence:bool\n    serving_read_models:bool\n    terminal_dependency:bool=False\n    execution_authority:bool=False\n\ndef build_oracle_live_runtime_state(state,sequence,accepting_intelligence,serving_read_models):\n    if state not in RUNTIME_STATES or int(sequence)<0:\n        raise ValueError("valid Oracle runtime state and sequence required")\n    active=state in ("STARTING","RUNNING","DEGRADED","RECOVERING")\n    return OracleLiveRuntimeState(\n        state,int(sequence),active,bool(accepting_intelligence),bool(serving_read_models),False,False\n    )\n\ndef verify_ois_046_oracle_live_runtime_state_model():\n    x=build_oracle_live_runtime_state("RUNNING",1,True,True)\n    return x.active and not x.terminal_dependency and not x.execution_authority and x.state=="RUNNING"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_046_runtime_state import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_046_oracle_live_runtime_state_model())\n\n    def test_stopped_not_active(self):\n        self.assertFalse(build_oracle_live_runtime_state("STOPPED",0,False,False).active)\n\n    def test_invalid_state(self):\n        with self.assertRaises(ValueError):\n            build_oracle_live_runtime_state("BAD",0,False,False)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-046 CERTIFICATION TEST");print(" ORACLE LIVE RUNTIME STATE MODEL");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle Live Runtime state model certified")\n    print("[DONE] OIS-046 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_045_live_adapter_gate")
    if getattr(upstream, "verify_ois_045_live_adapter_activation_coverage_gate")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_046_runtime_state import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-046 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-046 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
