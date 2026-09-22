from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_028_market_behavior_history.py"
TEST_PATH=ROOT/"test_olr_028_market_behavior_history.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_027_accumulated_calibration_state import AccumulatedCalibrationState\n\nOLR_028_BUILD_ID="OLR-028"\nOLR_028_REVISION="OLR_028_MARKET_BEHAVIOR_HISTORY_V1"\n\n@dataclass(frozen=True)\nclass MarketBehaviorHistory:\n    market_ticker:str\n    samples:int\n    calibration_bias:float\n    mean_brier_score:float\n    reliability_weight:float\n    behavior_class:str\n    stable:bool\n    advisory_only:bool=True\n    execution_authority:bool=False\n\ndef classify_market_behavior(state:AccumulatedCalibrationState):\n    if not state.mature:\n        behavior="insufficient_history"\n        stable=False\n    else:\n        b=state.calibration_bias\n        if abs(b)<.03:behavior="well_calibrated"\n        elif b>=.03:behavior="historically_underpriced_yes"\n        else:behavior="historically_overpriced_yes"\n        stable=state.reliability_weight>=.2\n    return MarketBehaviorHistory(\n        state.market_ticker,state.samples,state.calibration_bias,\n        state.mean_brier_score,state.reliability_weight,\n        behavior,stable,True,False\n    )\n\ndef verify_olr_028_market_behavior_history():\n    s=AccumulatedCalibrationState("KX",10,.55,.60,.2,.3,.05,.2,True,False)\n    x=classify_market_behavior(s)\n    return x.behavior_class=="historically_underpriced_yes" and x.advisory_only and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_027_accumulated_calibration_state import AccumulatedCalibrationState\nfrom qseries_v2.oracle_learning_runtime.olr_028_market_behavior_history import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_028_market_behavior_history())\n    def test_immature(self):\n        s=AccumulatedCalibrationState("KX",2,.5,.5,.25,.5,0,.04,False,False)\n        self.assertEqual(classify_market_behavior(s).behavior_class,"insufficient_history")\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-028 CERTIFICATION TEST");print(" MARKET BEHAVIOR HISTORY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Historical market-behavior classification certified")\n    print("[DONE] OLR-028 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-028 INSTALLER")
    print(" MARKET BEHAVIOR HISTORY")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_027_accumulated_calibration_state')
    verifier=getattr(upstream,'verify_olr_027_accumulated_calibration_state')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-027 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_028_market_behavior_history import *"
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
        print("[ROLLBACK] OLR-028 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-028 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
