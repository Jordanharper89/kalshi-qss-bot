from pathlib import Path
import os,sys,subprocess,importlib

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_learning_runtime"
MOD_PATH=PKG/"olr_044_final_production_certification_gate.py"
TEST_PATH=ROOT/"test_olr_044_final_production_certification_gate.py"
INIT_PATH=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .olr_041_learning_health_model import verify_olr_041_learning_health_model\nfrom .olr_042_deterministic_learning_replay import verify_olr_042_deterministic_learning_replay\nfrom .olr_043_production_learning_integrity_verification import verify_olr_043_production_learning_integrity_verification\n\nOLR_044_BUILD_ID="OLR-044"\nOLR_044_REVISION="OLR_044_FINAL_PRODUCTION_CERTIFICATION_GATE_V1"\n\n@dataclass(frozen=True)\nclass OLR044Certification:\n    start_build:str\n    end_build:str\n    runtime_role:str\n    read_only_reasoning_boundary:bool\n    execution_authority:bool\n    ready_for_freeze:bool\n\ndef certify_olr_final_production_boundary():\n    if not all((\n        verify_olr_041_learning_health_model(),\n        verify_olr_042_deterministic_learning_replay(),\n        verify_olr_043_production_learning_integrity_verification(),\n    )):\n        raise RuntimeError("Final OLR production certification failed")\n    return OLR044Certification(\n        "OLR-001","OLR-044",\n        "continuous_outcome_grounded_learning_calibration_and_bounded_feedback",\n        True,False,True\n    )\n\ndef verify_olr_044_final_production_certification_gate():\n    x=certify_olr_final_production_boundary()\n    return x.ready_for_freeze and x.read_only_reasoning_boundary and x.execution_authority is False\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_044_final_production_certification_gate import *\n\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_044_final_production_certification_gate())\n    def test_boundary(self):\n        x=certify_olr_final_production_boundary()\n        self.assertEqual(x.end_build,"OLR-044");self.assertFalse(x.execution_authority)\n\nif __name__=="__main__":\n    print("="*72);print(" OLR-044 CERTIFICATION TEST");print(" FINAL PRODUCTION CERTIFICATION GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OLR-001 through OLR-044 production learning boundary certified")\n    print("[PASS] Ready for final OLR freeze")\n    print("[DONE] OLR-044 CERTIFIED")\n'


def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*72)
    print(" OLR-044 INSTALLER")
    print(" FINAL PRODUCTION CERTIFICATION GATE")
    print("="*72)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))
    upstream=importlib.import_module('qseries_v2.oracle_learning_runtime.olr_043_production_learning_integrity_verification')
    verifier=getattr(upstream,'verify_olr_043_production_learning_integrity_verification')
    if verifier() is not True:
        raise RuntimeError("Certified upstream verification failed")
    print("[PASS] Certified OLR-043 upstream boundary verified")

    affected=(MOD_PATH,TEST_PATH,INIT_PATH,)
    backups={path_obj:(path_obj.read_bytes() if path_obj.exists() else None) for path_obj in affected}

    try:
        write_exact(MOD_PATH,MODULE_SOURCE)
        write_exact(TEST_PATH,TEST_SOURCE)

        current=INIT_PATH.read_text(encoding="utf-8") if INIT_PATH.exists() else ""
        export_line="from .olr_044_final_production_certification_gate import *"
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
        print("[ROLLBACK] OLR-044 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD_PATH.relative_to(ROOT))
    print("[PASS] Wrote:",TEST_PATH.name)
    print("[PASS] Updated:",INIT_PATH.relative_to(ROOT))
    print("[DONE] OLR-044 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
