from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_024_calibration_behavior_feedback_envelope.py"
TEST_PATH=ROOT/"test_olr_024_calibration_behavior_feedback_envelope.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_023_market_behavior_calibration_profile import MarketBehaviorCalibrationProfile\n\nOLR_024_BUILD_ID="OLR-024"\nOLR_024_REVISION="OLR_024_CALIBRATION_BEHAVIOR_FEEDBACK_ENVELOPE_V1"\n\n@dataclass(frozen=True)\nclass CalibrationBehaviorFeedbackEnvelope:\n    market_ticker:str\n    samples:int\n    reliability_weight:float\n    calibration_bias:float\n    bounded_probability_adjustment:float\n    behavior_signal_available:bool\n    advisory_only:bool=True\n    execution_authority:bool=False\n\ndef build_calibration_behavior_feedback(profile:MarketBehaviorCalibrationProfile,max_adjustment=.05,min_samples=5):\n    if profile.samples < int(min_samples):\n        adjustment=0.0\n        available=False\n    else:\n        raw=profile.calibration_bias*profile.reliability_weight\n        cap=abs(float(max_adjustment))\n        adjustment=max(-cap,min(cap,raw))\n        available=True\n    return CalibrationBehaviorFeedbackEnvelope(\n        profile.market_ticker,profile.samples,profile.reliability_weight,\n        profile.calibration_bias,adjustment,available,True,False\n    )\n\ndef verify_olr_024_calibration_behavior_feedback_envelope():\n    p=MarketBehaviorCalibrationProfile("KX",50,.55,.60,.2,.3,.05,1.0,True,False)\n    x=build_calibration_behavior_feedback(p)\n    return x.behavior_signal_available and 0 < x.bounded_probability_adjustment <= .05 and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_023_market_behavior_calibration_profile import MarketBehaviorCalibrationProfile\nfrom qseries_v2.oracle_learning_runtime.olr_024_calibration_behavior_feedback_envelope import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_024_calibration_behavior_feedback_envelope())\n    def test_low_sample_abstains(self):\n        p=MarketBehaviorCalibrationProfile("KX",2,.8,1,.1,.2,.2,.04,True,False)\n        x=build_calibration_behavior_feedback(p)\n        self.assertFalse(x.behavior_signal_available);self.assertEqual(x.bounded_probability_adjustment,0.0)\n    def test_bounded(self):\n        p=MarketBehaviorCalibrationProfile("KX",100,.1,1,.1,.1,.9,1,True,False)\n        self.assertLessEqual(abs(build_calibration_behavior_feedback(p).bounded_probability_adjustment),.05)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-024 CERTIFICATION TEST");print(" CALIBRATION + BEHAVIOR FEEDBACK ENVELOPE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Sample-gated bounded advisory feedback certified")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-024 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-024 INSTALLER")
    print(" CALIBRATION BEHAVIOR FEEDBACK ENVELOPE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_023_market_behavior_calibration_profile')
    verifier=getattr(upstream,'verify_olr_023_market_behavior_calibration_profile')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-023 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_024_calibration_behavior_feedback_envelope import *"
        if export_line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")

        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)

    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():
                    path_obj.unlink()
            else:
                path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-024 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-024 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
