from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_040_multi_adapter_orchestration_gate.py"
TEST = ROOT / "test_ois_040_multi_adapter_orchestration_capability_gate.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_036_adapter_registry import verify_ois_036_production_adapter_registry_orchestration\nfrom .ois_037_adapter_health import verify_ois_037_adapter_readiness_health\nfrom .ois_038_universe_reconciliation import verify_ois_038_full_universe_reconciliation\nfrom .ois_039_multi_adapter_event_coordination import verify_ois_039_multi_adapter_event_stream_coordination\n\nOIS_040_BUILD_ID="OIS-040"\nOIS_040_REVISION="OIS_040_MULTI_ADAPTER_ORCHESTRATION_CAPABILITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass MultiAdapterOrchestrationCertification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_ois_036_through_040():\n    checks=(\n        verify_ois_036_production_adapter_registry_orchestration(),\n        verify_ois_037_adapter_readiness_health(),\n        verify_ois_038_full_universe_reconciliation(),\n        verify_ois_039_multi_adapter_event_stream_coordination(),\n    )\n    if not all(checks):\n        raise RuntimeError("multi-adapter orchestration certification failed")\n    return MultiAdapterOrchestrationCertification(\n        tuple("OIS-%03d"%i for i in range(36,41)),\n        "production_adapter_registry_health_full_universe_reconciliation_multi_adapter_event_coordination",\n        "adapter_specific_live_activation_and_production_coverage_expansion",\n        True,\n    )\n\ndef verify_ois_040_multi_adapter_orchestration_capability_gate():\n    c=certify_ois_036_through_040()\n    return c.certified and len(c.builds)==5 and c.next_capability=="adapter_specific_live_activation_and_production_coverage_expansion"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_040_multi_adapter_orchestration_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_040_multi_adapter_orchestration_capability_gate())\n\n    def test_five(self):\n        self.assertEqual(len(certify_ois_036_through_040().builds),5)\n\n    def test_next(self):\n        self.assertEqual(\n            certify_ois_036_through_040().next_capability,\n            "adapter_specific_live_activation_and_production_coverage_expansion",\n        )\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-040 CERTIFICATION TEST");print(" MULTI-ADAPTER ORCHESTRATION CAPABILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OIS-036 through OIS-040 production multi-adapter orchestration capability certified")\n    print("[PASS] Next capability: adapter-specific live activation and production coverage expansion")\n    print("[DONE] OIS-040 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_039_multi_adapter_event_coordination")
    if getattr(upstream, "verify_ois_039_multi_adapter_event_stream_coordination")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_040_multi_adapter_orchestration_gate import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-040 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-040 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
