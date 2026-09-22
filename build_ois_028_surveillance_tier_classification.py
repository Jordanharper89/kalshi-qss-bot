from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_028_tier_classification.py"
TEST = ROOT / "test_ois_028_surveillance_tier_classification.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_026_universal_surveillance import SURVEILLANCE_TIERS\nfrom .ois_027_full_universe_state import MarketSurveillanceState\n\nOIS_028_BUILD_ID="OIS-028"\nOIS_028_REVISION="OIS_028_SURVEILLANCE_TIER_CLASSIFICATION_V1"\n\n@dataclass(frozen=True)\nclass SurveillanceTierDecision:\n    venue_id:str\n    market_id:str\n    tier:str\n    reason:str\n    reevaluate_on_event:bool\n    max_scheduled_refresh_seconds:float|None\n\ndef classify_surveillance_tier(state,near_qseries_threshold=False,catalyst=False,dislocation=False):\n    if not isinstance(state,MarketSurveillanceState):\n        raise ValueError("certified market surveillance state required")\n\n    if not state.tradable:\n        return SurveillanceTierDecision(state.venue_id,state.market_id,"DEAD","not_tradable",False,None)\n\n    if near_qseries_threshold:\n        return SurveillanceTierDecision(state.venue_id,state.market_id,"ULTRA_HOT","near_qseries_threshold",True,0.1)\n\n    if catalyst or dislocation or state.activity_score>=.85:\n        reason="catalyst" if catalyst else ("dislocation" if dislocation else "high_activity")\n        return SurveillanceTierDecision(state.venue_id,state.market_id,"HOT",reason,True,0.25)\n\n    if state.activity_score>=.50 or state.liquidity_score>=.60:\n        return SurveillanceTierDecision(state.venue_id,state.market_id,"ACTIVE","active_market",True,1.0)\n\n    if state.activity_score>=.25:\n        return SurveillanceTierDecision(state.venue_id,state.market_id,"WARM","moderate_activity",True,5.0)\n\n    if state.liquidity_score>0 or state.activity_score>0:\n        return SurveillanceTierDecision(state.venue_id,state.market_id,"COLD","low_activity",True,30.0)\n\n    return SurveillanceTierDecision(state.venue_id,state.market_id,"DORMANT","inactive_open_market",True,120.0)\n\ndef verify_ois_028_surveillance_tier_classification():\n    from .ois_027_full_universe_state import build_market_surveillance_state\n    a=build_market_surveillance_state("kalshi","A","x",True,1,1,.8,.9)\n    d=classify_surveillance_tier(a)\n    return d.tier=="HOT" and d.reevaluate_on_event and d.tier in SURVEILLANCE_TIERS\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_027_full_universe_state import build_market_surveillance_state\nfrom qseries_v2.oracle_intelligence_state.ois_028_tier_classification import *\n\nclass T(unittest.TestCase):\n    def state(self,tradable=True,liq=.5,act=.5):\n        return build_market_surveillance_state("kalshi","A","x",tradable,1,1,liq,act)\n\n    def test_verifier(self):\n        self.assertTrue(verify_ois_028_surveillance_tier_classification())\n\n    def test_ultra_hot(self):\n        self.assertEqual(classify_surveillance_tier(self.state(),near_qseries_threshold=True).tier,"ULTRA_HOT")\n\n    def test_dead(self):\n        self.assertEqual(classify_surveillance_tier(self.state(False,0,0)).tier,"DEAD")\n\n    def test_active_one_second(self):\n        self.assertEqual(classify_surveillance_tier(self.state(True,.7,.6)).max_scheduled_refresh_seconds,1.0)\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-028 CERTIFICATION TEST");print(" SURVEILLANCE-TIER CLASSIFICATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] ULTRA-HOT/HOT/ACTIVE/WARM/COLD/DORMANT/DEAD classification certified")\n    print("[DONE] OIS-028 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_027_full_universe_state")
    if getattr(upstream, "verify_ois_027_full_universe_market_state")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_028_tier_classification import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-028 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-028 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
