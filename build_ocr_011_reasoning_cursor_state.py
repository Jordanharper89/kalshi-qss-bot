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

BUILD_ID='OCR-011'
TITLE='REASONING CURSOR STATE'
REVISION='OCR_011_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_011_reasoning_cursor_state.py'
TEST=ROOT/'test_ocr_011_reasoning_cursor_state.py'
EXPORTS=('OCR_011_BUILD_ID', 'OCR_011_REVISION', 'ReasoningCursorState', 'empty_reasoning_cursor', 'load_reasoning_cursor', 'save_reasoning_cursor', 'advance_reasoning_cursor', 'verify_ocr_011_reasoning_cursor_state')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport json,os\n\nOCR_011_BUILD_ID="OCR-011"\nOCR_011_REVISION="OCR_011_REASONING_CURSOR_STATE_V1"\n\n@dataclass(frozen=True)\nclass ReasoningCursorState:\n    order_column:str\n    order_value:str\n    observation_id:str\n    batches_completed:int\n    observations_processed:int\n\ndef empty_reasoning_cursor():\n    return ReasoningCursorState("","","",0,0)\n\ndef load_reasoning_cursor(path):\n    p=Path(path)\n    if not p.is_file():\n        return empty_reasoning_cursor()\n    d=json.loads(p.read_text(encoding="utf-8"))\n    return ReasoningCursorState(\n        str(d.get("order_column") or ""),\n        str(d.get("order_value") or ""),\n        str(d.get("observation_id") or ""),\n        int(d.get("batches_completed",0)),\n        int(d.get("observations_processed",0)),\n    )\n\ndef save_reasoning_cursor(path,state):\n    p=Path(path)\n    p.parent.mkdir(parents=True,exist_ok=True)\n    tmp=p.with_suffix(p.suffix+".tmp")\n    payload={\n        "order_column":state.order_column,\n        "order_value":state.order_value,\n        "observation_id":state.observation_id,\n        "batches_completed":state.batches_completed,\n        "observations_processed":state.observations_processed,\n    }\n    tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":")),encoding="utf-8",newline="\\n")\n    os.replace(tmp,p)\n\ndef advance_reasoning_cursor(state,order_column,order_value,observation_id,processed_count):\n    if int(processed_count)<1:\n        raise ValueError("processed_count must be positive")\n    return ReasoningCursorState(\n        str(order_column),\n        str(order_value),\n        str(observation_id),\n        state.batches_completed+1,\n        state.observations_processed+int(processed_count),\n    )\n\ndef verify_ocr_011_reasoning_cursor_state():\n    import tempfile\n    with tempfile.TemporaryDirectory() as d:\n        p=Path(d)/"cursor.json"\n        s=advance_reasoning_cursor(empty_reasoning_cursor(),"sequence_number","42","obs42",3)\n        save_reasoning_cursor(p,s)\n        return load_reasoning_cursor(p)==s\n'
TEST_SOURCE='import tempfile,unittest\nfrom pathlib import Path\nfrom qseries_v2.oracle_continuous_reasoning.ocr_011_reasoning_cursor_state import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_011_reasoning_cursor_state())\n    def test_empty(self):\n        with tempfile.TemporaryDirectory() as d:\n            self.assertEqual(load_reasoning_cursor(Path(d)/"none.json"),empty_reasoning_cursor())\nif __name__=="__main__":\n    print("="*72);print(" OCR-011 CERTIFICATION TEST");print(" REASONING CURSOR STATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Durable atomic reasoning cursor state certified");print("[DONE] OCR-011 CERTIFIED")\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_010_capability_gate')
        if getattr(m,'verify_ocr_010_market_aware_continuous_reasoning_capability_gate')() is not True:
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
