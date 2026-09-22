from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_023_market_behavior_calibration_profile.py"
TEST_PATH=ROOT/"test_olr_023_market_behavior_calibration_profile.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom statistics import mean\nfrom .olr_022_outcome_calibration_record import OutcomeCalibrationRecord\n\nOLR_023_BUILD_ID="OLR-023"\nOLR_023_REVISION="OLR_023_MARKET_BEHAVIOR_CALIBRATION_PROFILE_V1"\n\n@dataclass(frozen=True)\nclass MarketBehaviorCalibrationProfile:\n    market_ticker:str\n    samples:int\n    mean_probability:float\n    empirical_yes_rate:float\n    mean_brier_score:float\n    mean_absolute_error:float\n    calibration_bias:float\n    reliability_weight:float\n    advisory_only:bool=True\n    execution_authority:bool=False\n\ndef build_market_behavior_calibration_profile(market_ticker:str,records):\n    rows=tuple(r for r in records if isinstance(r,OutcomeCalibrationRecord) and r.market_ticker==market_ticker)\n    if not rows:\n        return MarketBehaviorCalibrationProfile(str(market_ticker),0,.5,.5,.25,.5,0.0,0.0,True,False)\n    mp=mean(r.probability for r in rows)\n    yr=mean(r.outcome for r in rows)\n    bs=mean(r.brier_score for r in rows)\n    ae=mean(r.absolute_error for r in rows)\n    weight=min(1.0,len(rows)/50.0)\n    return MarketBehaviorCalibrationProfile(\n        str(market_ticker),len(rows),mp,yr,bs,ae,yr-mp,weight,True,False\n    )\n\ndef verify_olr_023_market_behavior_calibration_profile():\n    r1=OutcomeCalibrationRecord("KX",.7,1,.09,.3,"p",True,False)\n    r2=OutcomeCalibrationRecord("KX",.6,0,.36,.6,"p",True,False)\n    x=build_market_behavior_calibration_profile("KX",(r1,r2))\n    return x.samples==2 and x.advisory_only and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import OutcomeCalibrationRecord\nfrom qseries_v2.oracle_learning_runtime.olr_023_market_behavior_calibration_profile import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_023_market_behavior_calibration_profile())\n    def test_empty_is_neutral(self):\n        x=build_market_behavior_calibration_profile("KX",())\n        self.assertEqual(x.reliability_weight,0.0);self.assertEqual(x.calibration_bias,0.0)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-023 CERTIFICATION TEST");print(" MARKET-BEHAVIOR CALIBRATION PROFILE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Outcome calibration + market behavior profile certified")\n    print("[DONE] OLR-023 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-023 INSTALLER")
    print(" MARKET BEHAVIOR CALIBRATION PROFILE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record')
    verifier=getattr(upstream,'verify_olr_022_outcome_calibration_record')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-022 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_023_market_behavior_calibration_profile import *"
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
        print("[ROLLBACK] OLR-023 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-023 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
