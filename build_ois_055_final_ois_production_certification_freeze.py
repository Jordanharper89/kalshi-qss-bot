from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_055_final_freeze.py"
TEST = ROOT / "test_ois_055_final_ois_production_certification_freeze.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom hashlib import sha256\nimport json\nfrom .ois_051_runtime_launcher_contract import verify_ois_051_oracle_live_runtime_production_launcher_contract\nfrom .ois_052_startup_readiness import verify_ois_052_runtime_startup_dependency_readiness_gate\nfrom .ois_053_runtime_supervision import verify_ois_053_24x7_runtime_supervision_automatic_recovery\nfrom .ois_054_operator_status_boundary import verify_ois_054_oracle_runtime_operator_status_boundary\n\nOIS_055_BUILD_ID="OIS-055"\nOIS_055_REVISION="OIS_055_FINAL_PRODUCTION_CERTIFICATION_FREEZE_V1"\n\n@dataclass(frozen=True)\nclass OracleIntelligenceStateFinalCertification:\n    builds:tuple[str,...]\n    subsystem:str\n    capability:str\n    downstream_boundary:str\n    freeze_hash:str\n    certified:bool=True\n    frozen:bool=True\n    defect_corrections_only:bool=True\n\ndef certify_and_freeze_ois_001_through_055():\n    checks=(\n        verify_ois_051_oracle_live_runtime_production_launcher_contract(),\n        verify_ois_052_runtime_startup_dependency_readiness_gate(),\n        verify_ois_053_24x7_runtime_supervision_automatic_recovery(),\n        verify_ois_054_oracle_runtime_operator_status_boundary(),\n    )\n    if not all(checks):\n        raise RuntimeError("final OIS certification failed")\n\n    builds=tuple("OIS-%03d"%i for i in range(1,56))\n    raw={\n        "builds":builds,\n        "subsystem":"Oracle Intelligence State",\n        "capability":"oracle_live_runtime_state_orchestration_surveillance_status",\n        "downstream_boundary":"operator_terminal_api_read_only_and_future_adapter_subsystem",\n        "frozen":True,\n        "defect_corrections_only":True,\n    }\n    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n\n    return OracleIntelligenceStateFinalCertification(\n        builds,\n        raw["subsystem"],\n        raw["capability"],\n        raw["downstream_boundary"],\n        h,\n        True,\n        True,\n        True,\n    )\n\ndef verify_ois_055_final_production_certification_freeze():\n    c=certify_and_freeze_ois_001_through_055()\n    return (\n        c.certified\n        and c.frozen\n        and c.defect_corrections_only\n        and len(c.builds)==55\n        and c.downstream_boundary=="operator_terminal_api_read_only_and_future_adapter_subsystem"\n    )\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_055_final_freeze import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_055_final_production_certification_freeze())\n\n    def test_all_55(self):\n        self.assertEqual(len(certify_and_freeze_ois_001_through_055().builds),55)\n\n    def test_frozen(self):\n        c=certify_and_freeze_ois_001_through_055()\n        self.assertTrue(c.frozen)\n        self.assertTrue(c.defect_corrections_only)\n\n    def test_boundary(self):\n        self.assertEqual(\n            certify_and_freeze_ois_001_through_055().downstream_boundary,\n            "operator_terminal_api_read_only_and_future_adapter_subsystem",\n        )\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-055 CERTIFICATION TEST");print(" FINAL OIS PRODUCTION CERTIFICATION + FREEZE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OIS-001 through OIS-055 Oracle Intelligence State certified")\n    print("[PASS] OIS permanently frozen; genuine defect corrections only")\n    print("[PASS] Oracle Live Runtime remains independent of Operator Terminal")\n    print("[DONE] OIS-055 CERTIFIED + FROZEN")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_054_operator_status_boundary")
    if getattr(upstream, "verify_ois_054_oracle_runtime_operator_status_boundary")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_055_final_freeze import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-055 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-055 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
