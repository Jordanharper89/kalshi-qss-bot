from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_026_universal_surveillance.py"
TEST = ROOT / "test_ois_026_universal_venue_surveillance_foundation.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom types import MappingProxyType\n\nOIS_026_BUILD_ID="OIS-026"\nOIS_026_REVISION="OIS_026_UNIVERSAL_VENUE_SURVEILLANCE_FOUNDATION_V1"\n\nSURVEILLANCE_TIERS=("ULTRA_HOT","HOT","ACTIVE","WARM","COLD","DORMANT","DEAD")\n\n@dataclass(frozen=True)\nclass VenueSurveillancePolicy:\n    venue_id:str\n    entire_universe_required:bool=True\n    event_driven_preferred:bool=True\n    active_max_refresh_seconds:float=1.0\n    terminal_dependency:bool=False\n    execution_authority:bool=False\n\n@dataclass(frozen=True)\nclass SurveillanceUniverseIdentity:\n    venue_id:str\n    adapter_id:str\n    category_scope:str\n\ndef build_venue_surveillance_policy(venue_id):\n    if not venue_id:\n        raise ValueError("venue_id required")\n    return VenueSurveillancePolicy(venue_id)\n\ndef build_surveillance_universe_identity(venue_id,adapter_id,category_scope="ALL"):\n    if not venue_id or not adapter_id or not category_scope:\n        raise ValueError("complete surveillance universe identity required")\n    return SurveillanceUniverseIdentity(venue_id,adapter_id,category_scope)\n\ndef build_ois_026_certification_manifest():\n    return MappingProxyType({\n        "build_id":OIS_026_BUILD_ID,\n        "revision":OIS_026_REVISION,\n        "entire_universe_required":True,\n        "event_driven_preferred":True,\n        "active_max_refresh_seconds":1.0,\n        "tiers":SURVEILLANCE_TIERS,\n        "execution":False,\n        "terminal_dependency":False,\n    })\n\ndef verify_ois_026_universal_venue_surveillance_foundation():\n    p=build_venue_surveillance_policy("kalshi")\n    u=build_surveillance_universe_identity("kalshi","kalshi_universal","ALL")\n    return (\n        p.entire_universe_required\n        and p.event_driven_preferred\n        and p.active_max_refresh_seconds==1.0\n        and not p.terminal_dependency\n        and not p.execution_authority\n        and u.category_scope=="ALL"\n        and len(SURVEILLANCE_TIERS)==7\n    )\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_026_universal_surveillance import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_026_universal_venue_surveillance_foundation())\n\n    def test_entire_universe_required(self):\n        self.assertTrue(build_venue_surveillance_policy("kalshi").entire_universe_required)\n\n    def test_active_one_second(self):\n        self.assertEqual(build_venue_surveillance_policy("kalshi").active_max_refresh_seconds,1.0)\n\n    def test_no_execution(self):\n        self.assertFalse(build_venue_surveillance_policy("kalshi").execution_authority)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-026 CERTIFICATION TEST");print(" UNIVERSAL VENUE SURVEILLANCE FOUNDATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Universal full-venue surveillance foundation certified")\n    print("[DONE] OIS-026 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_025_unified_runtime_gate")
    if getattr(upstream, "verify_ois_025_unified_24x7_oracle_runtime_certification_gate")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_026_universal_surveillance import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-026 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-026 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
