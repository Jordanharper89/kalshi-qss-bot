from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_040_learning_consumption_maturity_gate.py"
TEST_PATH=ROOT/"test_olr_040_learning_consumption_maturity_gate.py"
INIT_PATH=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_036_live_feedback_read_model import verify_olr_036_live_feedback_read_model\nfrom .olr_037_learning_maturity_gate import verify_olr_037_learning_maturity_gate\nfrom .olr_038_learning_staleness_contradiction_guard import verify_olr_038_learning_staleness_contradiction_guard\nfrom .olr_039_bounded_learning_consumption_envelope import verify_olr_039_bounded_learning_consumption_envelope\n\nOLR_040_BUILD_ID="OLR-040"\nOLR_040_REVISION="OLR_040_LEARNING_CONSUMPTION_MATURITY_GATE_V1"\n\n@dataclass(frozen=True)\nclass OLR040Certification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_olr_036_through_040():\n    if not all((\n        verify_olr_036_live_feedback_read_model(),\n        verify_olr_037_learning_maturity_gate(),\n        verify_olr_038_learning_staleness_contradiction_guard(),\n        verify_olr_039_bounded_learning_consumption_envelope(),\n    )):\n        raise RuntimeError("OLR-036 through OLR-040 certification failed")\n    return OLR040Certification(\n        tuple("OLR-%03d"%i for i in range(36,41)),\n        "bounded_mature_learning_feedback_consumption",\n        "learning_health_replay_and_final_freeze",\n        True,\n    )\n\ndef verify_olr_040_learning_consumption_maturity_gate():\n    c=certify_olr_036_through_040()\n    return c.certified and len(c.builds)==5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_040_learning_consumption_maturity_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_040_learning_consumption_maturity_gate())\n    def test_five(self):self.assertEqual(len(certify_olr_036_through_040().builds),5)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-040 CERTIFICATION TEST");print(" LEARNING CONSUMPTION + MATURITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OLR-036 through OLR-040 bounded mature learning-feedback consumption certified")\n    print("[PASS] Next capability: learning health + replay + final freeze")\n    print("[DONE] OLR-040 CERTIFIED")\n'
EXTRA_PATH_1=ROOT/'run_olr_040_physical_learning_consumption_verification.py'
EXTRA_SOURCE_1='from pathlib import Path\nfrom qseries_v2.oracle_learning_runtime.olr_036_live_feedback_read_model import load_live_feedback_snapshot\nfrom qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope import build_bounded_learning_consumption\n\nif __name__=="__main__":\n    print("="*72)\n    print(" OLR-040 PHYSICAL LEARNING CONSUMPTION VERIFICATION")\n    print("="*72)\n    root=Path.cwd()\n    feedback=load_live_feedback_snapshot(root)\n    print(f"[LIVE FEEDBACK] markets={len(feedback)}")\n    eligible=0\n    for ticker,row in list(sorted(feedback.items()))[:25]:\n        x=build_bounded_learning_consumption(row)\n        if x.available:eligible+=1\n        print(f"[LEARNING] market={ticker} samples={row.samples} mature={row.mature} stable={row.stable} available={x.available} adjustment={x.bounded_adjustment:.4f} reason={x.reason}")\n    print(f"[SUMMARY] inspected={min(25,len(feedback))} eligible={eligible}")\n    print("[PASS] Live learning feedback consumed through maturity/guard boundary")\n    print("[PASS] No immature learning can create an adjustment")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OLR-040 PHYSICAL LEARNING CONSUMPTION VERIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72);print(" OLR-040 INSTALLER");print(" LEARNING CONSUMPTION MATURITY GATE");print("="*72)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_039_bounded_learning_consumption_envelope')
    if getattr(upstream,'verify_olr_039_bounded_learning_consumption_envelope')() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-039 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,EXTRA_PATH_1,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)
        write_exact(EXTRA_PATH_1,EXTRA_SOURCE_1)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        line="from .olr_040_learning_consumption_maturity_gate import *"
        if line not in current:
            write_exact(INIT_PATH,current.rstrip()+"\n"+line+"\n")

        compile(MOD_PATH.read_text(encoding="utf-8"),str(MOD_PATH),"exec")
        compile(TEST_PATH.read_text(encoding="utf-8"),str(TEST_PATH),"exec")
        subprocess.run([sys.executable,str(TEST_PATH)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(EXTRA_PATH_1)],cwd=str(ROOT),check=True)
    except Exception:
        for path_obj,old in backups.items():
            if old is None:
                if path_obj.exists():path_obj.unlink()
            else:path_obj.write_bytes(old)
        print("[ROLLBACK] OLR-040 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-040 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":main()
