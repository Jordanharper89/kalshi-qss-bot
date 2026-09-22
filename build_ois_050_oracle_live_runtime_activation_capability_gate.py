from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_050_runtime_activation_gate.py"
TEST = ROOT / "test_ois_050_oracle_live_runtime_activation_capability_gate.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_046_runtime_state import verify_ois_046_oracle_live_runtime_state_model\nfrom .ois_047_runtime_activation import verify_ois_047_oracle_live_runtime_activation_controller\nfrom .ois_048_service_health_aggregation import verify_ois_048_runtime_service_registry_health_aggregation\nfrom .ois_049_runtime_status_read_model import verify_ois_049_oracle_runtime_status_read_model\n\nOIS_050_BUILD_ID="OIS-050"\nOIS_050_REVISION="OIS_050_ORACLE_LIVE_RUNTIME_ACTIVATION_CAPABILITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass OracleLiveRuntimeActivationCertification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_ois_046_through_050():\n    checks=(\n        verify_ois_046_oracle_live_runtime_state_model(),\n        verify_ois_047_oracle_live_runtime_activation_controller(),\n        verify_ois_048_runtime_service_registry_health_aggregation(),\n        verify_ois_049_oracle_runtime_status_read_model(),\n    )\n    if not all(checks):\n        raise RuntimeError("Oracle Live Runtime activation capability certification failed")\n    return OracleLiveRuntimeActivationCertification(\n        tuple("OIS-%03d"%i for i in range(46,51)),\n        "oracle_live_runtime_state_activation_service_health_and_status_read_model",\n        "oracle_live_runtime_launcher_supervision_and_final_ois_certification",\n        True,\n    )\n\ndef verify_ois_050_oracle_live_runtime_activation_capability_gate():\n    c=certify_ois_046_through_050()\n    return c.certified and len(c.builds)==5 and c.next_capability=="oracle_live_runtime_launcher_supervision_and_final_ois_certification"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_050_runtime_activation_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_050_oracle_live_runtime_activation_capability_gate())\n\n    def test_five(self):\n        self.assertEqual(len(certify_ois_046_through_050().builds),5)\n\n    def test_next(self):\n        self.assertEqual(\n            certify_ois_046_through_050().next_capability,\n            "oracle_live_runtime_launcher_supervision_and_final_ois_certification",\n        )\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-050 CERTIFICATION TEST");print(" ORACLE LIVE RUNTIME ACTIVATION CAPABILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OIS-046 through OIS-050 Oracle Live Runtime activation/status capability certified")\n    print("[PASS] Next capability: Oracle Live Runtime launcher, supervision, and final OIS certification")\n    print("[DONE] OIS-050 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_049_runtime_status_read_model")
    if getattr(upstream, "verify_ois_049_oracle_runtime_status_read_model")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_050_runtime_activation_gate import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-050 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-050 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
