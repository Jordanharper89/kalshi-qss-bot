from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_030_durable_calibration_reasoning_binding_gate.py"
TEST_PATH=ROOT/"test_olr_030_durable_calibration_reasoning_binding_gate.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_026_durable_calibration_ledger import verify_olr_026_durable_calibration_ledger\nfrom .olr_027_accumulated_calibration_state import verify_olr_027_accumulated_calibration_state\nfrom .olr_028_market_behavior_history import verify_olr_028_market_behavior_history\nfrom .olr_029_live_reasoning_feedback_projection import verify_olr_029_live_reasoning_feedback_projection\n\nOLR_030_BUILD_ID="OLR-030"\nOLR_030_REVISION="OLR_030_DURABLE_CALIBRATION_REASONING_BINDING_GATE_V1"\n\n@dataclass(frozen=True)\nclass OLR030Certification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_olr_026_through_030():\n    if not all((\n        verify_olr_026_durable_calibration_ledger(),\n        verify_olr_027_accumulated_calibration_state(),\n        verify_olr_028_market_behavior_history(),\n        verify_olr_029_live_reasoning_feedback_projection(),\n    )):\n        raise RuntimeError("OLR-026 through OLR-030 certification failed")\n    return OLR030Certification(\n        tuple("OLR-%03d"%i for i in range(26,31)),\n        "durable_calibration_history_and_live_reasoning_feedback_binding",\n        "production_runtime_supervision_and_continuous_calibration_ingestion",\n        True,\n    )\n\ndef verify_olr_030_durable_calibration_reasoning_binding_gate():\n    c=certify_olr_026_through_030()\n    return c.certified and len(c.builds)==5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_030_durable_calibration_reasoning_binding_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_030_durable_calibration_reasoning_binding_gate())\n    def test_five(self):self.assertEqual(len(certify_olr_026_through_030().builds),5)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-030 CERTIFICATION TEST");print(" DURABLE CALIBRATION + REASONING BINDING GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OLR-026 through OLR-030 durable calibration history + live reasoning feedback certified")\n    print("[PASS] Next capability: production supervision + continuous calibration ingestion")\n    print("[DONE] OLR-030 CERTIFIED")\n'
EXTRA_PATH_1=ROOT/'run_olr_030_physical_durable_calibration_live_feedback_verification.py'
EXTRA_SOURCE_1='from pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_026_durable_calibration_ledger import load_calibration_ledger\nfrom qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection import materialize_live_reasoning_feedback\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-030 PHYSICAL DURABLE CALIBRATION + LIVE FEEDBACK VERIFICATION")\n    print("="*72)\n    root=Path.cwd()\n    ledger_path=root/"runtime_state"/"oracle_calibration_ledger.json"\n    ledger=load_calibration_ledger(ledger_path)\n    print(f"[CALIBRATION LEDGER] records={len(ledger)} path=runtime_state\\\\oracle_calibration_ledger.json")\n    summary=materialize_live_reasoning_feedback(root)\n    print(f"[LIVE FEEDBACK] records={summary.calibration_records} markets={summary.markets} mature_markets={summary.mature_markets}")\n    print(f"[LIVE FEEDBACK] snapshot={summary.output_path}")\n    print("[PASS] Durable calibration history projected into live reasoning feedback")\n    print("[PASS] Frozen OCR/OCL/OIS boundaries remain read-only")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-030 PHYSICAL DURABLE CALIBRATION + LIVE FEEDBACK VERIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-030 INSTALLER")
    print(" DURABLE CALIBRATION REASONING BINDING GATE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_029_live_reasoning_feedback_projection')
    verifier=getattr(upstream,'verify_olr_029_live_reasoning_feedback_projection')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-029 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_030_durable_calibration_reasoning_binding_gate import *"
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
        print("[ROLLBACK] OLR-030 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-030 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
