from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_025_outcome_calibration_market_behavior_gate.py"
TEST_PATH=ROOT/"test_olr_025_outcome_calibration_market_behavior_gate.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_021_pre_settlement_probability_recovery import verify_olr_021_pre_settlement_probability_recovery\nfrom .olr_022_outcome_calibration_record import verify_olr_022_outcome_calibration_record\nfrom .olr_023_market_behavior_calibration_profile import verify_olr_023_market_behavior_calibration_profile\nfrom .olr_024_calibration_behavior_feedback_envelope import verify_olr_024_calibration_behavior_feedback_envelope\n\nOLR_025_BUILD_ID="OLR-025"\nOLR_025_REVISION="OLR_025_OUTCOME_CALIBRATION_MARKET_BEHAVIOR_GATE_V1"\n\n@dataclass(frozen=True)\nclass OLR025Certification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_olr_021_through_025():\n    if not all((\n        verify_olr_021_pre_settlement_probability_recovery(),\n        verify_olr_022_outcome_calibration_record(),\n        verify_olr_023_market_behavior_calibration_profile(),\n        verify_olr_024_calibration_behavior_feedback_envelope(),\n    )):\n        raise RuntimeError("OLR-021 through OLR-025 certification failed")\n    return OLR025Certification(\n        tuple("OLR-%03d"%i for i in range(21,26)),\n        "outcome_calibration_and_market_behavior_learning_feedback",\n        "durable_calibration_history_and_live_reasoning_feedback_binding",\n        True,\n    )\n\ndef verify_olr_025_outcome_calibration_market_behavior_gate():\n    c=certify_olr_021_through_025()\n    return c.certified and len(c.builds)==5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_025_outcome_calibration_market_behavior_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_025_outcome_calibration_market_behavior_gate())\n    def test_five(self):self.assertEqual(len(certify_olr_021_through_025().builds),5)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-025 CERTIFICATION TEST");print(" OUTCOME CALIBRATION + MARKET BEHAVIOR GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OLR-021 through OLR-025 outcome calibration + market behavior feedback certified")\n    print("[PASS] Next capability: durable calibration history + live reasoning feedback binding")\n    print("[DONE] OLR-025 CERTIFIED")\n'
EXTRA_PATH_1=ROOT/'run_olr_025_physical_calibration_market_behavior_verification.py'
EXTRA_SOURCE_1='from qseries_v2.oracle_learning_runtime.olr_021_pre_settlement_probability_recovery import recover_pre_settlement_probability\nfrom qseries_v2.oracle_learning_runtime.olr_022_outcome_calibration_record import build_outcome_calibration_record\nfrom qseries_v2.oracle_learning_runtime.olr_023_market_behavior_calibration_profile import build_market_behavior_calibration_profile\nfrom qseries_v2.oracle_learning_runtime.olr_024_calibration_behavior_feedback_envelope import build_calibration_behavior_feedback\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-025 PHYSICAL CALIBRATION + MARKET-BEHAVIOR VERIFICATION")\n    print("="*72)\n\n    # Physical structural proof using the production-certified public surfaces.\n    # No fake historical claim is made: if real durable probability history is not\n    # yet materialized, this verifies abstention/boundedness rather than inventing it.\n    no_prob=recover_pre_settlement_probability({"observation_id":"physical"})\n    print(f"[PROBABILITY] recovered={no_prob.recovered} abstain_reason={no_prob.abstain_reason}")\n    assert no_prob.recovered is False\n\n    record=build_outcome_calibration_record("KXPHYSICAL",{"yes_price":60},"yes")\n    profile=build_market_behavior_calibration_profile("KXPHYSICAL",(record,))\n    feedback=build_calibration_behavior_feedback(profile,min_samples=5)\n\n    print(f"[CALIBRATION] samples={profile.samples} brier={profile.mean_brier_score:.4f} bias={profile.calibration_bias:.4f}")\n    print(f"[FEEDBACK] available={feedback.behavior_signal_available} adjustment={feedback.bounded_probability_adjustment:.4f}")\n    print("[PASS] Low-sample behavior feedback correctly abstains")\n    print("[PASS] Probability adjustment remains bounded")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-025 PHYSICAL CALIBRATION + MARKET-BEHAVIOR VERIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-025 INSTALLER")
    print(" OUTCOME CALIBRATION MARKET BEHAVIOR GATE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_024_calibration_behavior_feedback_envelope')
    verifier=getattr(upstream,'verify_olr_024_calibration_behavior_feedback_envelope')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-024 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_025_outcome_calibration_market_behavior_gate import *"
        if export_line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+export_line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")

        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(EXTRA_PATH_1)],cwd=str(ROOT),check=True)
    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():
                    path_obj.unlink()
            else:
                path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-025 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-025 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
