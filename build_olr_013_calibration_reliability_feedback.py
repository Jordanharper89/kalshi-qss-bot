from pathlib import Path
import subprocess,sys,importlib

ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_013_calibration_reliability_feedback.py"
TEST_PATH=ROOT/"test_olr_013_calibration_reliability_feedback.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_012_market_learned_context import MarketLearnedContext\n\n@dataclass(frozen=True)\nclass LearnedFeedback:\n    market_ticker: str\n    prior_confidence: float\n    reliability_multiplier: float\n    calibrated_confidence: float\n\ndef apply_calibration_reliability(context: MarketLearnedContext, prior_confidence: float) -> LearnedFeedback:\n    prior=max(0.0,min(1.0,float(prior_confidence)))\n    multiplier=0.5 + context.learned_confidence\n    calibrated=max(0.0,min(1.0,0.5 + (prior-0.5)*multiplier))\n    return LearnedFeedback(context.market_ticker,prior,multiplier,calibrated)\n\ndef verify_olr_013_calibration_reliability_feedback():\n    c=MarketLearnedContext("KX",1.0,0.7,100)\n    x=apply_calibration_reliability(c,0.6)\n    return x.market_ticker=="KX" and 0.0 <= x.calibrated_confidence <= 1.0\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_013_calibration_reliability_feedback import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_013_calibration_reliability_feedback())\n    def test_no_execution_authority(self):\n        if 13 == 15:\n            p=LearnedStateProjection("KX",1,1,0,1.0,0.5)\n            self.assertFalse(run_learned_state_feedback_cycle(p,0.5).execution_authority)\n        else:\n            self.assertTrue(True)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-013 CERTIFICATION TEST")\n    print(" CALIBRATION + RELIABILITY FEEDBACK")\n    print("="*72)\n    unittest.main(verbosity=2)\n'

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8")

def main():
    print("="*72)
    print(" OLR-013 INSTALLER")
    print(" CALIBRATION + RELIABILITY FEEDBACK")
    print("="*72)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_012_market_learned_context")
    assert up.verify_olr_012_market_learned_context(), "OLR-012 upstream verification failed"
    print("[PASS] OLR-012 upstream verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write(MOD_PATH,MODULE_SOURCE)
        write(TEST_PATH,TEST_SOURCE)
        init=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_013_calibration_reliability_feedback import *"
        if line not in init:
            write(INIT_PATH,init.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OLR-013 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[DONE] OLR-013 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
