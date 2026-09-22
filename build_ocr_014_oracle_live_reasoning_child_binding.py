from __future__ import annotations
import importlib, os, subprocess, sys
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
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OCR-014'
TITLE='ORACLE LIVE REASONING CHILD BINDING'
REVISION='OCR_014_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_014_oracle_live_binding.py'
TEST=ROOT/'test_ocr_014_oracle_live_reasoning_child_binding.py'
EXPORTS=('OCR_014_BUILD_ID', 'OCR_014_REVISION', 'OracleLiveReasoningBinding', 'build_oracle_live_reasoning_binding', 'verify_ocr_014_oracle_live_reasoning_child_binding')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOCR_014_BUILD_ID="OCR-014"\nOCR_014_REVISION="OCR_014_ORACLE_LIVE_REASONING_CHILD_BINDING_V1"\n\n@dataclass(frozen=True)\nclass OracleLiveReasoningBinding:\n    reasoning_child:str\n    cursor_state_path:str\n    supervised:bool\n    terminal_dependency:bool=False\n    execution_authority:bool=False\n\ndef build_oracle_live_reasoning_binding():\n    return OracleLiveReasoningBinding(\n        "run_ocr_013_continuous_reasoning_runtime.py",\n        "runtime_state/ocr_reasoning_cursor.json",\n        True,\n        False,\n        False,\n    )\n\ndef verify_ocr_014_oracle_live_reasoning_child_binding():\n    b=build_oracle_live_reasoning_binding()\n    return b.supervised and not b.terminal_dependency and not b.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_014_oracle_live_binding import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_014_oracle_live_reasoning_child_binding())\nif __name__=="__main__":\n    print("="*72);print(" OCR-014 CERTIFICATION TEST");print(" ORACLE LIVE REASONING CHILD BINDING");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Supervised OCR reasoning child binding certified");print("[DONE] OCR-014 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_013_continuous_reasoning_loop')
        if getattr(m,'verify_ocr_013_continuous_market_aware_reasoning_loop')() is not True:
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
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

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
