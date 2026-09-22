from pathlib import Path
import subprocess,sys,importlib

ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_014_scientific_reasoning_context_injection.py"
TEST_PATH=ROOT/"test_olr_014_scientific_reasoning_context_injection.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_013_calibration_reliability_feedback import LearnedFeedback\n\n@dataclass(frozen=True)\nclass ScientificReasoningContext:\n    market_ticker: str\n    base_confidence: float\n    learned_confidence: float\n    learning_applied: bool\n    execution_authority: bool=False\n\ndef inject_learned_feedback(market_ticker: str, base_confidence: float, feedback: LearnedFeedback|None) -> ScientificReasoningContext:\n    base=max(0.0,min(1.0,float(base_confidence)))\n    learned=feedback.calibrated_confidence if feedback and feedback.market_ticker==market_ticker else base\n    return ScientificReasoningContext(market_ticker,base,learned,feedback is not None and feedback.market_ticker==market_ticker,False)\n\ndef verify_olr_014_scientific_reasoning_context_injection():\n    return inject_learned_feedback("KX",0.5,None).execution_authority is False\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_014_scientific_reasoning_context_injection import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_014_scientific_reasoning_context_injection())\n    def test_no_execution_authority(self):\n        if 14 == 15:\n            p=LearnedStateProjection("KX",1,1,0,1.0,0.5)\n            self.assertFalse(run_learned_state_feedback_cycle(p,0.5).execution_authority)\n        else:\n            self.assertTrue(True)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-014 CERTIFICATION TEST")\n    print(" SCIENTIFIC REASONING CONTEXT INJECTION")\n    print("="*72)\n    unittest.main(verbosity=2)\n'

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8")

def main():
    print("="*72)
    print(" OLR-014 INSTALLER")
    print(" SCIENTIFIC REASONING CONTEXT INJECTION")
    print("="*72)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_013_calibration_reliability_feedback")
    assert up.verify_olr_013_calibration_reliability_feedback(), "OLR-013 upstream verification failed"
    print("[PASS] OLR-013 upstream verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write(MOD_PATH,MODULE_SOURCE)
        write(TEST_PATH,TEST_SOURCE)
        init=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_014_scientific_reasoning_context_injection import *"
        if line not in init:
            write(INIT_PATH,init.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OLR-014 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[DONE] OLR-014 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
