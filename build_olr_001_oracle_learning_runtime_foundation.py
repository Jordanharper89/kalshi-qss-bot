from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_learning_runtime"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OLR-001'
TITLE='ORACLE LEARNING RUNTIME FOUNDATION'
REVISION='OLR_001_PRODUCTION_V1'
MODULE=PACKAGE/'olr_001_foundation.py'
TEST=ROOT/'test_olr_001_oracle_learning_runtime_foundation.py'
EXPORTS=('OLR_001_BUILD_ID', 'OLR_001_REVISION', 'LearningRuntimeFoundation', 'build_learning_runtime_foundation', 'verify_olr_001_oracle_learning_runtime_foundation')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nimport importlib\nOLR_001_BUILD_ID="OLR-001"\nOLR_001_REVISION="OLR_001_ORACLE_LEARNING_RUNTIME_FOUNDATION_V1"\n\n@dataclass(frozen=True)\nclass LearningRuntimeFoundation:\n    frozen_learner:str\n    live_reasoning:str\n    kalshi_adapter:str\n    outcome_required:bool\n    execution_authority:bool=False\n    upstream_mutation:bool=False\n\ndef build_learning_runtime_foundation():\n    checks=(\n      ("qseries_v2.oracle_continuous_learner.ocl_030_final_freeze_gate","verify_ocl_030_continuous_learner_runtime_final_freeze_gate","OCL-030"),\n      ("qseries_v2.oracle_continuous_reasoning.ocr_015_production_gate","verify_ocr_015_continuous_reasoning_production_capability_gate","OCR-015"),\n      ("qseries_v2.oracle_adapters.kalshi.oad_055_kalshi_production_freeze","verify_oad_055_kalshi_production_adapter_freeze_gate","OAD-055"),\n    )\n    for mod,ver,label in checks:\n        if getattr(importlib.import_module(mod),ver)() is not True:\n            raise RuntimeError(label+" verification failed")\n    return LearningRuntimeFoundation("OCL-030","OCR-015","OAD-055",True,False,False)\n\ndef verify_olr_001_oracle_learning_runtime_foundation():\n    x=build_learning_runtime_foundation()\n    return x.outcome_required and not x.execution_authority and not x.upstream_mutation\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_learning_runtime.olr_001_foundation import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_olr_001_oracle_learning_runtime_foundation())\n    def test_outcomes_required(self):self.assertTrue(build_learning_runtime_foundation().outcome_required)\nif __name__=="__main__":\n    print("="*72);print(" OLR-001 CERTIFICATION TEST");print(" ORACLE LEARNING RUNTIME FOUNDATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Frozen OCL/OCR/OAD boundaries consumed read-only")\n    print("[PASS] Outcome-required learning enforced")\n    print("[DONE] OLR-001 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_030_final_freeze_gate')
        if getattr(m,'verify_ocl_030_continuous_learner_runtime_final_freeze_gate')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified frozen upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_learning_runtime."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
        run_test(TEST)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
