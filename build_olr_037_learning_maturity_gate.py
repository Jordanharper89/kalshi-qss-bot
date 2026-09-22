from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_037_learning_maturity_gate.py"
TEST_PATH=ROOT/"test_olr_037_learning_maturity_gate.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_036_live_feedback_read_model import LiveCalibrationFeedback\n\nOLR_037_BUILD_ID="OLR-037"\nOLR_037_REVISION="OLR_037_LEARNING_MATURITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass LearningMaturityDecision:\n    market_ticker:str\n    eligible:bool\n    reason:str\n    samples:int\n    reliability_weight:float\n    execution_authority:bool=False\n\ndef evaluate_learning_maturity(feedback:LiveCalibrationFeedback,min_samples=5,min_reliability=.10):\n    if feedback.samples<int(min_samples):\n        return LearningMaturityDecision(feedback.market_ticker,False,"insufficient_samples",feedback.samples,feedback.reliability_weight,False)\n    if not feedback.mature:\n        return LearningMaturityDecision(feedback.market_ticker,False,"not_mature",feedback.samples,feedback.reliability_weight,False)\n    if feedback.reliability_weight<float(min_reliability):\n        return LearningMaturityDecision(feedback.market_ticker,False,"insufficient_reliability",feedback.samples,feedback.reliability_weight,False)\n    if not feedback.stable:\n        return LearningMaturityDecision(feedback.market_ticker,False,"unstable_history",feedback.samples,feedback.reliability_weight,False)\n    return LearningMaturityDecision(feedback.market_ticker,True,"eligible",feedback.samples,feedback.reliability_weight,False)\n\ndef verify_olr_037_learning_maturity_gate():\n    f=LiveCalibrationFeedback("KX",10,.01,.2,.2,True,"well_calibrated",True,False)\n    return evaluate_learning_maturity(f).eligible\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import LiveCalibrationFeedback\nfrom qseries_v2.oracle_learning_runtime.olr_037_learning_maturity_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_037_learning_maturity_gate())\n    def test_low_sample_abstains(self):\n        f=LiveCalibrationFeedback("KX",1,0,.2,.02,False,"insufficient_history",False,False)\n        self.assertFalse(evaluate_learning_maturity(f).eligible)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-037 CERTIFICATION TEST");print(" LEARNING MATURITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Learning maturity + reliability gating certified")\n    print("[DONE] OLR-037 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-037 INSTALLER");print(" LEARNING MATURITY GATE");print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model')
    if getattr(upstream,'verify_olr_036_live_feedback_read_model')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-036 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_037_learning_maturity_gate import *"
        if line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-037 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-037 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
