from pathlib import Path
import subprocess,sys,importlib

ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_015_learned_state_feedback_runtime_gate.py"
TEST_PATH=ROOT/"test_olr_015_learned_state_feedback_runtime_gate.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_011_learned_state_read_projection import LearnedStateProjection\nfrom .olr_012_market_learned_context import build_market_learned_context\nfrom .olr_013_calibration_reliability_feedback import apply_calibration_reliability\nfrom .olr_014_scientific_reasoning_context_injection import inject_learned_feedback\n\n@dataclass(frozen=True)\nclass LearnedStateFeedbackRuntimeSummary:\n    market_ticker: str\n    learning_applied: bool\n    learned_confidence: float\n    execution_authority: bool\n\ndef run_learned_state_feedback_cycle(projection: LearnedStateProjection, base_confidence: float) -> LearnedStateFeedbackRuntimeSummary:\n    context=build_market_learned_context(projection)\n    feedback=apply_calibration_reliability(context,base_confidence)\n    reasoning=inject_learned_feedback(projection.market_ticker,base_confidence,feedback)\n    return LearnedStateFeedbackRuntimeSummary(reasoning.market_ticker,reasoning.learning_applied,reasoning.learned_confidence,False)\n\ndef verify_olr_015_learned_state_feedback_runtime_gate():\n    p=LearnedStateProjection("KXTEST",10,6,4,0.6,0.9)\n    x=run_learned_state_feedback_cycle(p,0.55)\n    return x.learning_applied and x.execution_authority is False\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_015_learned_state_feedback_runtime_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_olr_015_learned_state_feedback_runtime_gate())\n    def test_no_execution_authority(self):\n        if 15 == 15:\n            p=LearnedStateProjection("KX",1,1,0,1.0,0.5)\n            self.assertFalse(run_learned_state_feedback_cycle(p,0.5).execution_authority)\n        else:\n            self.assertTrue(True)\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-015 CERTIFICATION TEST")\n    print(" LEARNED-STATE FEEDBACK RUNTIME GATE")\n    print("="*72)\n    unittest.main(verbosity=2)\n'

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding="utf-8")

def main():
    print("="*72)
    print(" OLR-015 INSTALLER")
    print(" LEARNED-STATE FEEDBACK RUNTIME GATE")
    print("="*72)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_learning_runtime.olr_014_scientific_reasoning_context_injection")
    assert up.verify_olr_014_scientific_reasoning_context_injection(), "OLR-014 upstream verification failed"
    print("[PASS] OLR-014 upstream verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write(MOD_PATH,MODULE_SOURCE)
        write(TEST_PATH,TEST_SOURCE)
        init=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_015_learned_state_feedback_runtime_gate import *"
        if line not in init:
            write(INIT_PATH,init.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OLR-015 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[DONE] OLR-015 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
