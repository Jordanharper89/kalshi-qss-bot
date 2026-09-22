from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_022_outcome_calibration_record.py"
TEST_PATH=ROOT/"test_olr_022_outcome_calibration_record.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_021_pre_settlement_probability_recovery import recover_pre_settlement_probability\n\nOLR_022_BUILD_ID="OLR-022"\nOLR_022_REVISION="OLR_022_OUTCOME_CALIBRATION_RECORD_V1"\n\n@dataclass(frozen=True)\nclass OutcomeCalibrationRecord:\n    market_ticker:str\n    probability:float\n    outcome:float\n    brier_score:float\n    absolute_error:float\n    source_key:str\n    eligible:bool=True\n    execution_authority:bool=False\n\ndef build_outcome_calibration_record(market_ticker:str,observation:dict,result:str):\n    recovery=recover_pre_settlement_probability(observation)\n    if not recovery.recovered:\n        return None\n    r=str(result or "").strip().lower()\n    if r=="yes":outcome=1.0\n    elif r=="no":outcome=0.0\n    else:return None\n    p=float(recovery.probability)\n    return OutcomeCalibrationRecord(\n        str(market_ticker),p,outcome,(p-outcome)**2,abs(p-outcome),\n        recovery.source_key,True,False\n    )\n\ndef verify_olr_022_outcome_calibration_record():\n    x=build_outcome_calibration_record("KX",{"yes_price":80},"yes")\n    return x is not None and abs(x.brier_score-.04)<1e-12 and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_022_outcome_calibration_record())\n    def test_no_probability_abstains(self):self.assertIsNone(build_outcome_calibration_record("KX",{"x":1},"yes"))\n    def test_unresolved_abstains(self):self.assertIsNone(build_outcome_calibration_record("KX",{"yes_price":60},""))\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-022 CERTIFICATION TEST");print(" OUTCOME CALIBRATION RECORD");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Outcome-grounded Brier calibration record certified")\n    print("[DONE] OLR-022 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-022 INSTALLER")
    print(" OUTCOME CALIBRATION RECORD")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_021_pre_settlement_probability_recovery')
    verifier=getattr(upstream,'verify_olr_021_pre_settlement_probability_recovery')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-021 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_022_outcome_calibration_record import *"
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
        print("[ROLLBACK] OLR-022 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-022 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
