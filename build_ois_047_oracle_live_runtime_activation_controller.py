from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_047_runtime_activation.py"
TEST = ROOT / "test_ois_047_oracle_live_runtime_activation_controller.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_046_runtime_state import OracleLiveRuntimeState,build_oracle_live_runtime_state\n\nOIS_047_BUILD_ID="OIS-047"\nOIS_047_REVISION="OIS_047_ORACLE_LIVE_RUNTIME_ACTIVATION_CONTROLLER_V1"\n\n@dataclass(frozen=True)\nclass RuntimeActivationDecision:\n    previous_state:str\n    next_state:str\n    permitted:bool\n    reason:str\n\n_ALLOWED={\n    "STOPPED":("STARTING",),\n    "STARTING":("RUNNING","DEGRADED","STOPPED"),\n    "RUNNING":("DEGRADED","RECOVERING","STOPPED"),\n    "DEGRADED":("RUNNING","RECOVERING","STOPPED"),\n    "RECOVERING":("RUNNING","DEGRADED","STOPPED"),\n}\n\ndef evaluate_runtime_transition(current,next_state):\n    if not isinstance(current,OracleLiveRuntimeState):\n        raise ValueError("certified runtime state required")\n    permitted=next_state in _ALLOWED.get(current.state,())\n    return RuntimeActivationDecision(current.state,next_state,permitted,"allowed" if permitted else "invalid_transition")\n\ndef transition_runtime(current,next_state,accepting_intelligence,serving_read_models):\n    d=evaluate_runtime_transition(current,next_state)\n    if not d.permitted:\n        raise ValueError("runtime transition not permitted")\n    return build_oracle_live_runtime_state(next_state,current.sequence+1,accepting_intelligence,serving_read_models)\n\ndef verify_ois_047_oracle_live_runtime_activation_controller():\n    s=build_oracle_live_runtime_state("STOPPED",0,False,False)\n    a=transition_runtime(s,"STARTING",False,False)\n    r=transition_runtime(a,"RUNNING",True,True)\n    return r.state=="RUNNING" and r.sequence==2 and r.accepting_intelligence\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_046_runtime_state import build_oracle_live_runtime_state\nfrom qseries_v2.oracle_intelligence_state.ois_047_runtime_activation import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_047_oracle_live_runtime_activation_controller())\n\n    def test_invalid_transition(self):\n        s=build_oracle_live_runtime_state("STOPPED",0,False,False)\n        with self.assertRaises(ValueError):\n            transition_runtime(s,"RUNNING",True,True)\n\n    def test_sequence_advances(self):\n        s=build_oracle_live_runtime_state("STOPPED",0,False,False)\n        self.assertEqual(transition_runtime(s,"STARTING",False,False).sequence,1)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-047 CERTIFICATION TEST");print(" ORACLE LIVE RUNTIME ACTIVATION CONTROLLER");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Oracle Live Runtime activation transitions certified")\n    print("[DONE] OIS-047 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_046_runtime_state")
    if getattr(upstream, "verify_ois_046_oracle_live_runtime_state_model")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_047_runtime_activation import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-047 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-047 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
