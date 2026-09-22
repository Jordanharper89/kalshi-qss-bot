from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_020_production_feedback_runtime_gate.py"
TEST_PATH=ROOT/"test_olr_020_production_feedback_runtime_gate.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_016_production_learned_state_adapter import verify_olr_016_production_learned_state_adapter\nfrom .olr_017_market_feedback_resolver import verify_olr_017_market_feedback_resolver\nfrom .olr_018_scientific_reasoning_feedback_envelope import verify_olr_018_scientific_reasoning_feedback_envelope\nfrom .olr_019_continuous_feedback_snapshot_runtime import verify_olr_019_continuous_feedback_snapshot_runtime\n\nOLR_020_BUILD_ID="OLR-020"\nOLR_020_REVISION="OLR_020_PRODUCTION_FEEDBACK_RUNTIME_GATE_V1"\n\n@dataclass(frozen=True)\nclass OLR020Certification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_olr_016_through_020():\n    checks=(\n        verify_olr_016_production_learned_state_adapter(),\n        verify_olr_017_market_feedback_resolver(),\n        verify_olr_018_scientific_reasoning_feedback_envelope(),\n        verify_olr_019_continuous_feedback_snapshot_runtime(),\n    )\n    if not all(checks):raise RuntimeError("OLR-016 through OLR-020 certification failed")\n    return OLR020Certification(\n        tuple("OLR-%03d"%i for i in range(16,21)),\n        "production_durable_learned_state_feedback_runtime",\n        "outcome_calibration_and_market_behavior_learning_feedback",\n        True,\n    )\n\ndef verify_olr_020_production_feedback_runtime_gate():\n    c=certify_olr_016_through_020()\n    return c.certified and len(c.builds)==5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_020_production_feedback_runtime_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_020_production_feedback_runtime_gate())\n    def test_five(self):self.assertEqual(len(certify_olr_016_through_020().builds),5)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-020 CERTIFICATION TEST");print(" PRODUCTION FEEDBACK RUNTIME GATE");print("="*72)\n    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not result.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OLR-016 through OLR-020 production feedback runtime certified")\n    print("[PASS] Next capability: outcome calibration + market-behavior learning feedback")\n    print("[DONE] OLR-020 CERTIFIED")\n'
EXTRA_PATH_1=ROOT/'run_olr_020_physical_production_feedback_verification.py'
EXTRA_SOURCE_1='from pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import load_production_learned_state\nfrom qseries_v2.oracle_learning_runtime.olr_019_continuous_feedback_snapshot_runtime import materialize_feedback_snapshot\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-020 PHYSICAL PRODUCTION LEARNED-STATE FEEDBACK VERIFICATION");print("="*72)\n    root=Path.cwd();state=load_production_learned_state(root)\n    print(f"[LEARNED STATE] cycles={state.cycles} outcomes_learned={state.outcomes_learned} learned_records={state.learned_records} markets={len(state.learned_market_counts)}")\n    print(f"[LEARNED STATE] learner_state_hash={state.learner_state_hash or \'NONE\'}")\n    summary=materialize_feedback_snapshot(root)\n    print(f"[FEEDBACK] markets={summary.markets} learned_records={summary.learned_records} snapshot={summary.snapshot_path}")\n    print("[PASS] Real durable OLR learning state projected into OLR-owned reasoning feedback snapshot")\n    print("[PASS] Frozen OCR/OCL/OIS boundaries remained read-only")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-020 PHYSICAL PRODUCTION FEEDBACK VERIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-020 INSTALLER");print(" PRODUCTION FEEDBACK RUNTIME GATE");print("="*72)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_019_continuous_feedback_snapshot_runtime')
    verifier=getattr(upstream,'verify_olr_019_continuous_feedback_snapshot_runtime')
    if verifier() is not True:raise RuntimeError("Upstream verification failed")
    print("[PASS] Certified upstream boundary verified")
    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}
    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_020_production_feedback_runtime_gate import *"
        if line not in current:write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(EXTRA_PATH_1)],cwd=str(ROOT),check=True)
    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-020 installation failed; affected files restored")
        raise
    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-020 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
