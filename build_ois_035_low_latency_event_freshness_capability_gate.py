from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_035_low_latency_event_gate.py"
TEST = ROOT / "test_ois_035_low_latency_event_freshness_capability_gate.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_031_low_latency_event_intake import verify_ois_031_low_latency_canonical_event_intake\nfrom .ois_032_event_classification import verify_ois_032_market_event_classification\nfrom .ois_033_latency_telemetry import verify_ois_033_end_to_end_latency_telemetry\nfrom .ois_034_freshness_enforcement import verify_ois_034_freshness_staleness_enforcement\n\nOIS_035_BUILD_ID="OIS-035"\nOIS_035_REVISION="OIS_035_LOW_LATENCY_EVENT_FRESHNESS_CAPABILITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass LowLatencyEventFreshnessCertification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_ois_031_through_035():\n    checks=(\n        verify_ois_031_low_latency_canonical_event_intake(),\n        verify_ois_032_market_event_classification(),\n        verify_ois_033_end_to_end_latency_telemetry(),\n        verify_ois_034_freshness_staleness_enforcement(),\n    )\n    if not all(checks):\n        raise RuntimeError("low-latency event/freshness capability certification failed")\n    return LowLatencyEventFreshnessCertification(\n        tuple("OIS-%03d"%i for i in range(31,36)),\n        "low_latency_event_ingestion_classification_latency_telemetry_freshness_enforcement",\n        "production_adapter_expansion_and_full_universe_adapter_orchestration",\n        True,\n    )\n\ndef verify_ois_035_low_latency_event_freshness_capability_gate():\n    c=certify_ois_031_through_035()\n    return c.certified and len(c.builds)==5 and c.next_capability=="production_adapter_expansion_and_full_universe_adapter_orchestration"\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_035_low_latency_event_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_035_low_latency_event_freshness_capability_gate())\n\n    def test_five(self):\n        self.assertEqual(len(certify_ois_031_through_035().builds),5)\n\n    def test_next(self):\n        self.assertEqual(\n            certify_ois_031_through_035().next_capability,\n            "production_adapter_expansion_and_full_universe_adapter_orchestration",\n        )\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-035 CERTIFICATION TEST");print(" LOW-LATENCY EVENT + FRESHNESS CAPABILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OIS-031 through OIS-035 low-latency event/freshness capability certified")\n    print("[PASS] Next capability: production adapter expansion and full-universe adapter orchestration")\n    print("[DONE] OIS-035 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_034_freshness_enforcement")
    if getattr(upstream, "verify_ois_034_freshness_staleness_enforcement")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_035_low_latency_event_gate import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-035 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-035 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
