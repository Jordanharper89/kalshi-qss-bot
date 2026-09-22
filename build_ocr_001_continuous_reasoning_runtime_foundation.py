from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_continuous_reasoning"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OCR-001'
TITLE='CONTINUOUS REASONING RUNTIME FOUNDATION'
REVISION='OCR_001_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_001_foundation.py'
TEST=ROOT/'test_ocr_001_continuous_reasoning_runtime_foundation.py'
EXPORTS=('OCR_001_BUILD_ID', 'OCR_001_REVISION', 'ContinuousReasoningFoundation', 'verify_frozen_reasoning_boundaries', 'build_continuous_reasoning_foundation', 'verify_ocr_001_continuous_reasoning_runtime_foundation')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom hashlib import sha256\nimport importlib,json\n\nOCR_001_BUILD_ID="OCR-001"\nOCR_001_REVISION="OCR_001_CONTINUOUS_REASONING_RUNTIME_FOUNDATION_V1"\n\nFROZEN_BOUNDARIES=(\n    ("qseries_v2.oracle_continuous_intake.oci_010_capability_certification","verify_oci_010_continuous_intake_capability_certification_gate","OCI-010"),\n    ("qseries_v2.oracle_continuous_learner.ocl_030_final_freeze_gate","verify_ocl_030_continuous_learner_runtime_final_freeze_gate","OCL-030"),\n    ("qseries_v2.oracle_scientific_reasoning.osr_030_final_freeze","verify_osr_030_scientific_reasoning_final_certification_freeze","OSR-030"),\n    ("qseries_v2.oracle_intelligence_state.ois_055_final_freeze","verify_ois_055_final_production_certification_freeze","OIS-055"),\n)\n\n@dataclass(frozen=True)\nclass ContinuousReasoningFoundation:\n    frozen_boundaries:tuple[str,...]\n    mode:str\n    terminal_dependency:bool\n    execution_authority:bool\n    upstream_mutation:bool\n    foundation_hash:str\n\ndef _h(v):\n    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()\n\ndef verify_frozen_reasoning_boundaries():\n    verified=[]\n    for module_name,verifier_name,label in FROZEN_BOUNDARIES:\n        module=importlib.import_module(module_name)\n        verifier=getattr(module,verifier_name,None)\n        if not callable(verifier) or verifier() is not True:\n            raise RuntimeError("Frozen boundary failed: "+label)\n        verified.append(label)\n    return tuple(verified)\n\ndef build_continuous_reasoning_foundation():\n    boundaries=verify_frozen_reasoning_boundaries()\n    raw={"boundaries":boundaries,"mode":"continuous_read_only_reasoning_activation","terminal_dependency":False,\n         "execution_authority":False,"upstream_mutation":False}\n    return ContinuousReasoningFoundation(boundaries,raw["mode"],False,False,False,_h(raw))\n\ndef verify_ocr_001_continuous_reasoning_runtime_foundation():\n    f=build_continuous_reasoning_foundation()\n    return f.frozen_boundaries==("OCI-010","OCL-030","OSR-030","OIS-055") and not f.execution_authority and not f.upstream_mutation\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_001_foundation import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_ocr_001_continuous_reasoning_runtime_foundation())\n    def test_boundaries(self): self.assertEqual(len(build_continuous_reasoning_foundation().frozen_boundaries),4)\n    def test_read_only(self): self.assertFalse(build_continuous_reasoning_foundation().upstream_mutation)\nif __name__=="__main__":\n    print("="*72);print(" OCR-001 CERTIFICATION TEST");print(" CONTINUOUS REASONING RUNTIME FOUNDATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Frozen OCI/OCL/OSR/OIS boundaries consumed read-only")\n    print("[DONE] OCR-001 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_intelligence_state.ois_055_final_freeze')
        if getattr(m,'verify_ois_055_final_production_certification_freeze')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_continuous_reasoning."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":
    main()
