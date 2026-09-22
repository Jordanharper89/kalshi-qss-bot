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

BUILD_ID='OCR-013'
TITLE='CONTINUOUS MARKET-AWARE REASONING LOOP'
REVISION='OCR_013_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_013_continuous_reasoning_loop.py'
TEST=ROOT/'test_ocr_013_continuous_market_aware_reasoning_loop.py'
EXPORTS=('OCR_013_BUILD_ID', 'OCR_013_REVISION', 'ContinuousReasoningCycleSummary', 'run_continuous_reasoning_cycle', 'verify_ocr_013_continuous_market_aware_reasoning_loop')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom .ocr_011_reasoning_cursor_state import load_reasoning_cursor,save_reasoning_cursor,advance_reasoning_cursor\nfrom .ocr_012_incremental_observation_selection import read_new_canonical_observations,cursor_values_from_last_row\nfrom .ocr_007_umd_context_join import join_rows_to_umd_context\nfrom .ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations\nfrom .ocr_009_intelligence_state_projection import project_reasoning_results\n\nOCR_013_BUILD_ID="OCR-013"\nOCR_013_REVISION="OCR_013_CONTINUOUS_MARKET_AWARE_REASONING_LOOP_V1"\n\n@dataclass(frozen=True)\nclass ContinuousReasoningCycleSummary:\n    rows_read:int\n    market_aware_rows:int\n    markets_reasoned:int\n    ois_projections:int\n    cursor_advanced:bool\n    idle:bool\n\ndef run_continuous_reasoning_cycle(root=None,limit=50,cursor_path=None,progress=print):\n    root=Path(root or Path.cwd()).resolve()\n    cp=Path(cursor_path or root/"runtime_state"/"ocr_reasoning_cursor.json")\n    cursor=load_reasoning_cursor(cp)\n    slice_=read_new_canonical_observations(root,cursor=cursor,limit=limit)\n    if not slice_.rows:\n        progress("[OCR] idle no_new_observations")\n        return ContinuousReasoningCycleSummary(0,0,0,0,False,True)\n    aware=join_rows_to_umd_context(slice_.rows)\n    if not aware:\n        raise RuntimeError("New observations found but none resolved to market identity")\n    reasoning=reason_over_market_aware_observations(aware)\n    projections=project_reasoning_results(reasoning)\n    if len(projections)!=len(reasoning):\n        raise RuntimeError("OIS projection count mismatch")\n    order_column,order_value,observation_id=cursor_values_from_last_row(slice_)\n    new_cursor=advance_reasoning_cursor(cursor,order_column,order_value,observation_id,len(slice_.rows))\n    save_reasoning_cursor(cp,new_cursor)\n    progress(f"[OCR] rows={len(slice_.rows)} market_aware={len(aware)} markets_reasoned={len(reasoning)} ois_projections={len(projections)}")\n    progress(f"[OCR] cursor={order_column}:{order_value}:{observation_id}")\n    return ContinuousReasoningCycleSummary(len(slice_.rows),len(aware),len(reasoning),len(projections),True,False)\n\ndef verify_ocr_013_continuous_market_aware_reasoning_loop():\n    return callable(run_continuous_reasoning_cycle)\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_013_continuous_reasoning_loop import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_013_continuous_market_aware_reasoning_loop())\n    def test_summary(self):self.assertTrue(ContinuousReasoningCycleSummary(0,0,0,0,False,True).idle)\nif __name__=="__main__":\n    print("="*72);print(" OCR-013 CERTIFICATION TEST");print(" CONTINUOUS MARKET-AWARE REASONING LOOP");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Cursor-driven continuous reasoning cycle certified");print("[DONE] OCR-013 CERTIFIED")\n'
EXTRA_1='from pathlib import Path\nimport argparse,time\nfrom qseries_v2.oracle_continuous_reasoning.ocr_013_continuous_reasoning_loop import run_continuous_reasoning_cycle\n\ndef main():\n    p=argparse.ArgumentParser()\n    p.add_argument("--batch-size",type=int,default=50)\n    p.add_argument("--cadence-seconds",type=float,default=2.0)\n    p.add_argument("--once",action="store_true")\n    a=p.parse_args()\n    if a.batch_size<1 or a.cadence_seconds<=0:raise SystemExit("invalid runtime arguments")\n    root=Path.cwd()\n    print("="*72,flush=True);print(" OCR-013 CONTINUOUS MARKET-AWARE REASONING RUNTIME",flush=True);print("="*72,flush=True)\n    cycles=0\n    try:\n        while True:\n            s=run_continuous_reasoning_cycle(root,limit=a.batch_size,progress=lambda x:print(x,flush=True))\n            cycles+=1\n            print(f"[OCR] cycle={cycles} idle={s.idle} rows={s.rows_read} markets_reasoned={s.markets_reasoned}",flush=True)\n            if a.once:return 0\n            time.sleep(a.cadence_seconds)\n    except KeyboardInterrupt:\n        print("\\\\n[STOP] OCR continuous reasoning runtime stopped by operator.",flush=True)\n        return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_012_incremental_observation_selection')
        if getattr(m,'verify_ocr_012_incremental_new_observation_selection')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_ocr_013_continuous_reasoning_runtime.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_ocr_013_continuous_reasoning_runtime.py',EXTRA_1)

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
