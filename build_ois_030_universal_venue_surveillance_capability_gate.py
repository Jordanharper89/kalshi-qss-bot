from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_030_surveillance_gate.py"
TEST = ROOT / "test_ois_030_universal_venue_surveillance_capability_gate.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_026_universal_surveillance import verify_ois_026_universal_venue_surveillance_foundation\nfrom .ois_027_full_universe_state import verify_ois_027_full_universe_market_state\nfrom .ois_028_tier_classification import verify_ois_028_surveillance_tier_classification\nfrom .ois_029_tier_transition import verify_ois_029_surveillance_promotion_demotion_engine\n\nOIS_030_BUILD_ID="OIS-030"\nOIS_030_REVISION="OIS_030_UNIVERSAL_VENUE_SURVEILLANCE_CAPABILITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass UniversalVenueSurveillanceCertification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_ois_026_through_030():\n    checks=(\n        verify_ois_026_universal_venue_surveillance_foundation(),\n        verify_ois_027_full_universe_market_state(),\n        verify_ois_028_surveillance_tier_classification(),\n        verify_ois_029_surveillance_promotion_demotion_engine(),\n    )\n    if not all(checks):\n        raise RuntimeError("universal venue surveillance capability certification failed")\n\n    return UniversalVenueSurveillanceCertification(\n        tuple("OIS-%03d"%i for i in range(26,31)),\n        "universal_full_venue_surveillance_and_dynamic_market_tiering",\n        "low_latency_event_ingestion_latency_telemetry_and_adapter_expansion",\n        True,\n    )\n\ndef verify_ois_030_universal_venue_surveillance_capability_gate():\n    c=certify_ois_026_through_030()\n    return (\n        c.certified\n        and len(c.builds)==5\n        and c.next_capability=="low_latency_event_ingestion_latency_telemetry_and_adapter_expansion"\n    )\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_030_surveillance_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_030_universal_venue_surveillance_capability_gate())\n\n    def test_five(self):\n        self.assertEqual(len(certify_ois_026_through_030().builds),5)\n\n    def test_next(self):\n        self.assertEqual(\n            certify_ois_026_through_030().next_capability,\n            "low_latency_event_ingestion_latency_telemetry_and_adapter_expansion",\n        )\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-030 CERTIFICATION TEST");print(" UNIVERSAL VENUE SURVEILLANCE CAPABILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OIS-026 through OIS-030 universal full-venue surveillance capability certified")\n    print("[PASS] Next capability: low-latency event ingestion, latency telemetry, and adapter expansion")\n    print("[DONE] OIS-030 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_029_tier_transition")
    if getattr(upstream, "verify_ois_029_surveillance_promotion_demotion_engine")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_030_surveillance_gate import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-030 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-030 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
