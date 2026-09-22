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
    if marker in current:return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OCR-009'
TITLE='INTELLIGENCE STATE PROJECTION'
REVISION='OCR_009_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_009_intelligence_state_projection.py'
TEST=ROOT/'test_ocr_009_intelligence_state_projection.py'
EXPORTS=('OCR_009_BUILD_ID', 'OCR_009_REVISION', 'LiveIntelligenceProjection', 'project_reasoning_result_to_ois', 'project_reasoning_results', 'verify_ocr_009_intelligence_state_projection')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import build_osr_state_intake\n\nOCR_009_BUILD_ID="OCR-009"\nOCR_009_REVISION="OCR_009_INTELLIGENCE_STATE_PROJECTION_V1"\n\n@dataclass(frozen=True)\nclass LiveIntelligenceProjection:\n    market_ticker:str\n    ois_intake:object\n    source_osr_hash:str\n    read_only:bool=True\n    writes_frozen_ois:bool=False\n\ndef project_reasoning_result_to_ois(result):\n    s=result.osr_state\n    intake=build_osr_state_intake(result.market_ticker,s.reasoning_state,s.support,s.confidence,s.contradiction,s.abstain,s.state_hash)\n    return LiveIntelligenceProjection(result.market_ticker,intake,s.state_hash,True,False)\n\ndef project_reasoning_results(results):\n    return tuple(project_reasoning_result_to_ois(x) for x in results)\n\ndef verify_ocr_009_intelligence_state_projection():\n    from .ocr_007_umd_context_join import join_rows_to_umd_context\n    from .ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations\n    obs=join_rows_to_umd_context(({"observation_id":"1","ticker":"KXTEST"},{"observation_id":"2","ticker":"KXTEST"}))\n    x=project_reasoning_results(reason_over_market_aware_observations(obs))[0]\n    return x.ois_intake.read_only and x.read_only and not x.writes_frozen_ois\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_009_intelligence_state_projection())\nif __name__=="__main__":\n    print("="*72);print(" OCR-009 CERTIFICATION TEST");print(" INTELLIGENCE STATE PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Frozen OIS-002 read-only projection boundary certified");print("[DONE] OCR-009 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation')
        if getattr(m,'verify_ocr_008_continuous_scientific_reasoning_invocation')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT);backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_continuous_reasoning."+MODULE.stem
            sys.modules.pop(name,None);m=importlib.import_module(name)
            v=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if v() is not True:raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored");raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
