from pathlib import Path
import importlib, sys, subprocess

ROOT = Path.cwd()
PACKAGE = ROOT / "qseries_v2" / "oracle_intelligence_state"
MODULE = PACKAGE / "ois_029_tier_transition.py"
TEST = ROOT / "test_ois_029_surveillance_promotion_demotion_engine.py"
INIT = PACKAGE / "__init__.py"

MODULE_SOURCE = 'from dataclasses import dataclass\nfrom .ois_028_tier_classification import SurveillanceTierDecision\n\nOIS_029_BUILD_ID="OIS-029"\nOIS_029_REVISION="OIS_029_SURVEILLANCE_PROMOTION_DEMOTION_ENGINE_V1"\n\nTIER_ORDER=("DEAD","DORMANT","COLD","WARM","ACTIVE","HOT","ULTRA_HOT")\n\n@dataclass(frozen=True)\nclass TierTransition:\n    venue_id:str\n    market_id:str\n    previous_tier:str\n    next_tier:str\n    direction:str\n    reason:str\n\ndef transition_surveillance_tier(previous_tier,next_decision):\n    if previous_tier not in TIER_ORDER or not isinstance(next_decision,SurveillanceTierDecision):\n        raise ValueError("valid tier transition required")\n    p=TIER_ORDER.index(previous_tier)\n    n=TIER_ORDER.index(next_decision.tier)\n    direction="PROMOTE" if n>p else ("DEMOTE" if n<p else "HOLD")\n    return TierTransition(\n        next_decision.venue_id,next_decision.market_id,previous_tier,next_decision.tier,direction,next_decision.reason\n    )\n\ndef should_interrupt_schedule(transition):\n    return transition.direction=="PROMOTE" and transition.next_tier in ("HOT","ULTRA_HOT")\n\ndef verify_ois_029_surveillance_promotion_demotion_engine():\n    d=SurveillanceTierDecision("kalshi","A","HOT","dislocation",True,.25)\n    t=transition_surveillance_tier("ACTIVE",d)\n    return t.direction=="PROMOTE" and should_interrupt_schedule(t)\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_state.ois_028_tier_classification import SurveillanceTierDecision\nfrom qseries_v2.oracle_intelligence_state.ois_029_tier_transition import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_ois_029_surveillance_promotion_demotion_engine())\n\n    def test_demote(self):\n        d=SurveillanceTierDecision("kalshi","A","COLD","low_activity",True,30)\n        self.assertEqual(transition_surveillance_tier("ACTIVE",d).direction,"DEMOTE")\n\n    def test_hold(self):\n        d=SurveillanceTierDecision("kalshi","A","ACTIVE","active_market",True,1)\n        self.assertEqual(transition_surveillance_tier("ACTIVE",d).direction,"HOLD")\n\nif __name__=="__main__":\n    print("="*72);print(" OIS-029 CERTIFICATION TEST");print(" SURVEILLANCE PROMOTION + DEMOTION ENGINE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Dynamic surveillance promotion/demotion semantics certified")\n    print("[DONE] OIS-029 CERTIFIED")\n'

def main():
    upstream = importlib.import_module("qseries_v2.oracle_intelligence_state.ois_028_tier_classification")
    if getattr(upstream, "verify_ois_028_surveillance_tier_classification")() is not True:
        raise RuntimeError("Certified upstream verification failed")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}

    try:
        MODULE.write_text(MODULE_SOURCE, encoding="utf-8", newline="\n")
        TEST.write_text(TEST_SOURCE, encoding="utf-8", newline="\n")
        compile(MODULE_SOURCE, str(MODULE), "exec")
        compile(TEST_SOURCE, str(TEST), "exec")

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        line = "from .ois_029_tier_transition import *"
        if line not in current:
            INIT.write_text(current.rstrip() + "\n" + line + "\n", encoding="utf-8", newline="\n")

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        print("[DONE] OIS-029 INSTALLATION AND CERTIFICATION COMPLETE")

    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OIS-029 installation failed; affected files restored")
        raise

if __name__ == "__main__":
    main()
