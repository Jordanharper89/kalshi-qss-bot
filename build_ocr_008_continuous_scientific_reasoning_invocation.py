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

BUILD_ID='OCR-008'
TITLE='CONTINUOUS SCIENTIFIC REASONING INVOCATION'
REVISION='OCR_008_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_008_scientific_reasoning_invocation.py'
TEST=ROOT/'test_ocr_008_continuous_scientific_reasoning_invocation.py'
EXPORTS=('OCR_008_BUILD_ID', 'OCR_008_REVISION', 'LiveScientificReasoningResult', 'invoke_frozen_scientific_reasoning', 'reason_over_market_aware_observations', 'verify_ocr_008_continuous_scientific_reasoning_invocation')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_scientific_reasoning.osr_028_cross_capability_synthesis import CapabilityReasoningState,synthesize_capabilities\nfrom qseries_v2.oracle_scientific_reasoning.osr_029_intelligence_state import build_oracle_scientific_intelligence_state,verify_oracle_scientific_intelligence_state\n\nOCR_008_BUILD_ID="OCR-008"\nOCR_008_REVISION="OCR_008_CONTINUOUS_SCIENTIFIC_REASONING_INVOCATION_V1"\n\n@dataclass(frozen=True)\nclass LiveScientificReasoningResult:\n    market_ticker:str\n    observation_count:int\n    osr_state:object\n    read_only:bool=True\n\ndef invoke_frozen_scientific_reasoning(market_ticker,observations):\n    rows=tuple(observations)\n    if not market_ticker or not rows:raise ValueError("market and observations required")\n    event_types={str((x.source_row.get("observation_type") or x.source_row.get("event_type") or "")).lower() for x in rows}\n    n=len(rows)\n    diversity=max(1,len(event_types))\n    support=min(0.95,0.45+min(n,20)/40.0)\n    confidence=min(0.95,0.50+min(diversity,4)*0.08+min(n,20)/100.0)\n    contradiction=max(0.0,min(0.35,(diversity-1)*0.05))\n    abstain=n<2\n    cap=CapabilityReasoningState("live_market_observation",support,confidence,contradiction,abstain)\n    synthesis=synthesize_capabilities((cap,))\n    state=build_oracle_scientific_intelligence_state(market_ticker,synthesis)\n    if not verify_oracle_scientific_intelligence_state(state):raise RuntimeError("Frozen OSR state verification failed")\n    return LiveScientificReasoningResult(market_ticker,n,state,True)\n\ndef reason_over_market_aware_observations(observations):\n    groups={}\n    for x in observations:groups.setdefault(x.market_ticker,[]).append(x)\n    return tuple(invoke_frozen_scientific_reasoning(k,groups[k]) for k in sorted(groups))\n\ndef verify_ocr_008_continuous_scientific_reasoning_invocation():\n    from .ocr_007_umd_context_join import join_rows_to_umd_context\n    obs=join_rows_to_umd_context(({"observation_id":"1","ticker":"KXTEST"},{"observation_id":"2","ticker":"KXTEST"}))\n    r=reason_over_market_aware_observations(obs)\n    return len(r)==1 and r[0].osr_state.read_only and not r[0].osr_state.execution_allowed\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_008_continuous_scientific_reasoning_invocation())\n    def test_requires_market(self):\n        with self.assertRaises(ValueError):invoke_frozen_scientific_reasoning("",())\nif __name__=="__main__":\n    print("="*72);print(" OCR-008 CERTIFICATION TEST");print(" CONTINUOUS SCIENTIFIC REASONING INVOCATION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Frozen OSR-028/029 reasoning path invoked read-only");print("[DONE] OCR-008 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join')
        if getattr(m,'verify_ocr_007_umd_market_context_join')() is not True:
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
