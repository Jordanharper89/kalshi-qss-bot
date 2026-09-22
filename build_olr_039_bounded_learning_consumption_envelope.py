from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_039_bounded_learning_consumption_envelope.py"
TEST_PATH=ROOT/"test_olr_039_bounded_learning_consumption_envelope.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_036_live_feedback_read_model import LiveCalibrationFeedback\nfrom .olr_037_learning_maturity_gate import evaluate_learning_maturity\nfrom .olr_038_learning_staleness_contradiction_guard import evaluate_learning_guard\n\nOLR_039_BUILD_ID="OLR-039"\nOLR_039_REVISION="OLR_039_BOUNDED_LEARNING_CONSUMPTION_ENVELOPE_V1"\n\n@dataclass(frozen=True)\nclass BoundedLearningConsumptionEnvelope:\n    market_ticker:str\n    available:bool\n    reason:str\n    bounded_adjustment:float\n    samples:int\n    behavior_class:str\n    advisory_only:bool=True\n    execution_authority:bool=False\n\ndef build_bounded_learning_consumption(feedback:LiveCalibrationFeedback,updated_at=None,contradiction_score=0.0,max_adjustment=.05):\n    maturity=evaluate_learning_maturity(feedback)\n    if not maturity.eligible:\n        return BoundedLearningConsumptionEnvelope(feedback.market_ticker,False,maturity.reason,0.0,feedback.samples,feedback.behavior_class,True,False)\n    guard=evaluate_learning_guard(updated_at,contradiction_score=contradiction_score)\n    if not guard.allowed:\n        return BoundedLearningConsumptionEnvelope(feedback.market_ticker,False,guard.reason,0.0,feedback.samples,feedback.behavior_class,True,False)\n    cap=abs(float(max_adjustment))\n    raw=feedback.calibration_bias*feedback.reliability_weight\n    adj=max(-cap,min(cap,raw))\n    return BoundedLearningConsumptionEnvelope(feedback.market_ticker,True,"eligible",adj,feedback.samples,feedback.behavior_class,True,False)\n\ndef verify_olr_039_bounded_learning_consumption_envelope():\n    f=LiveCalibrationFeedback("KX",20,.10,.2,.4,True,"historically_underpriced_yes",True,False)\n    x=build_bounded_learning_consumption(f)\n    return x.available and 0 < x.bounded_adjustment <= .05 and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import LiveCalibrationFeedback\nfrom qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_039_bounded_learning_consumption_envelope())\n    def test_unmatured_zero(self):\n        f=LiveCalibrationFeedback("KX",1,.5,.5,.01,False,"insufficient_history",False,False)\n        self.assertEqual(build_bounded_learning_consumption(f).bounded_adjustment,0.0)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-039 CERTIFICATION TEST");print(" BOUNDED LEARNING CONSUMPTION ENVELOPE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Mature-only bounded advisory learning consumption certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-039 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-039 INSTALLER");print(" BOUNDED LEARNING CONSUMPTION ENVELOPE");print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_038_learning_staleness_contradiction_guard')
    if getattr(upstream,'verify_olr_038_learning_staleness_contradiction_guard')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-038 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_039_bounded_learning_consumption_envelope import *"
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
        print("[ROLLBACK] OLR-039 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-039 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
