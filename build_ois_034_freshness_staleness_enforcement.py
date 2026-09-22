from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_034_freshness_enforcement.py"
TEST = ROOT / "test_ois_034_freshness_staleness_enforcement.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_028_tier_classification import SurveillanceTierDecision\n\nOIS_034_BUILD_ID="OIS-034"\nOIS_034_REVISION="OIS_034_FRESHNESS_STALENESS_ENFORCEMENT_V1"\n\n@dataclass(frozen=True)\nclass FreshnessDecision:\n    tier:str\n    age_seconds:float\n    max_age_seconds:float|None\n    fresh:bool\n    stale:bool\n    block_handoff:bool\n\ndef evaluate_market_freshness(tier_decision,age_seconds):\n    if not isinstance(tier_decision,SurveillanceTierDecision):\n        raise ValueError("certified tier decision required")\n    age=float(age_seconds)\n    if age<0:\n        raise ValueError("age must be non-negative")\n    max_age=tier_decision.max_scheduled_refresh_seconds\n    if tier_decision.tier=="DEAD":\n        return FreshnessDecision("DEAD",age,None,True,False,True)\n    if max_age is None:\n        return FreshnessDecision(tier_decision.tier,age,None,True,False,False)\n    fresh=age<=max_age\n    return FreshnessDecision(tier_decision.tier,age,max_age,fresh,not fresh,not fresh)\n\ndef verify_ois_034_freshness_staleness_enforcement():\n    d=SurveillanceTierDecision("k","m","ACTIVE","active_market",True,1.0)\n    return evaluate_market_freshness(d,.8).fresh and evaluate_market_freshness(d,1.2).block_handoff\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_028_tier_classification import SurveillanceTierDecision\nfrom qseries_v2.oracle_intelligence_state.ois_034_freshness_enforcement import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_034_freshness_staleness_enforcement())\n\n    def test_active_one_second(self):\n        d=SurveillanceTierDecision("k","m","ACTIVE","x",True,1.0)\n        self.assertTrue(evaluate_market_freshness(d,1.01).stale)\n\n    def test_dead_blocks(self):\n        d=SurveillanceTierDecision("k","m","DEAD","x",False,None)\n        self.assertTrue(evaluate_market_freshness(d,100).block_handoff)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-034 CERTIFICATION TEST");print(" FRESHNESS + STALENESS ENFORCEMENT");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Tier-aware market freshness/staleness enforcement certified")\n    print("[DONE] OIS-034 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_033_latency_telemetry")
    if getattr(upstream, "verify_ois_033_end_to_end_latency_telemetry")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_034_freshness_enforcement import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-034 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-034 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
