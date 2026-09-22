from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_025_unified_runtime_gate.py"
TEST = ROOT / "test_ois_025_unified_24x7_oracle_runtime_certification_gate.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_021_unified_runtime import verify_ois_021_unified_oracle_runtime_composition\nfrom .ois_022_pipeline_orchestrator import verify_ois_022_continuous_pipeline_cycle_orchestrator\nfrom .ois_023_runtime_recovery import verify_ois_023_runtime_checkpoint_crash_recovery_coordination\nfrom .ois_024_service_activation import verify_ois_024_24x7_service_activation_health_boundary\n\nOIS_025_BUILD_ID="OIS-025"\nOIS_025_REVISION="OIS_025_UNIFIED_24X7_ORACLE_RUNTIME_CERTIFICATION_GATE_V1"\n\n@dataclass(frozen=True)\nclass UnifiedOracleRuntimeCertification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_ois_021_through_025():\n    checks=(\n        verify_ois_021_unified_oracle_runtime_composition(),\n        verify_ois_022_continuous_pipeline_cycle_orchestrator(),\n        verify_ois_023_runtime_checkpoint_crash_recovery_coordination(),\n        verify_ois_024_24x7_service_activation_health_boundary(),\n    )\n    if not all(checks): raise RuntimeError("unified Oracle Runtime certification failed")\n    return UnifiedOracleRuntimeCertification(\n        tuple("OIS-%03d"%i for i in range(21,26)),\n        "unified_24x7_oracle_runtime_wiring_and_service_activation",\n        "universal_venue_surveillance_and_opportunity_intelligence",\n        True,\n    )\n\ndef verify_ois_025_unified_24x7_oracle_runtime_certification_gate():\n    c=certify_ois_021_through_025()\n    return c.certified and len(c.builds)==5 and c.next_capability=="universal_venue_surveillance_and_opportunity_intelligence"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_025_unified_runtime_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ois_025_unified_24x7_oracle_runtime_certification_gate())\n    def test_five(self): self.assertEqual(len(certify_ois_021_through_025().builds),5)\n    def test_next(self): self.assertEqual(certify_ois_021_through_025().next_capability,"universal_venue_surveillance_and_opportunity_intelligence")\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-025 CERTIFICATION TEST");print(" UNIFIED 24/7 ORACLE RUNTIME CAPABILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OIS-021 through OIS-025 unified 24/7 Oracle Runtime capability certified")\n    print("[PASS] Next capability: universal venue surveillance and opportunity intelligence")\n    print("[DONE] OIS-025 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_024_service_activation")
    if getattr(upstream, "verify_ois_024_24x7_service_activation_health_boundary")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_025_unified_runtime_gate import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-025 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-025 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
