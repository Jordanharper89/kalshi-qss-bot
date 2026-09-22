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

BUILD_ID='OCR-010'
TITLE='MARKET-AWARE CONTINUOUS REASONING CAPABILITY GATE'
REVISION='OCR_010_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_010_capability_gate.py'
TEST=ROOT/'test_ocr_010_market_aware_continuous_reasoning_capability_gate.py'
EXPORTS=('OCR_010_BUILD_ID', 'OCR_010_REVISION', 'OCR010Certification', 'certify_ocr_006_through_010', 'verify_ocr_010_market_aware_continuous_reasoning_capability_gate')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .ocr_006_market_identity_recovery import verify_ocr_006_canonical_market_identity_recovery\nfrom .ocr_007_umd_context_join import verify_ocr_007_umd_market_context_join\nfrom .ocr_008_scientific_reasoning_invocation import verify_ocr_008_continuous_scientific_reasoning_invocation\nfrom .ocr_009_intelligence_state_projection import verify_ocr_009_intelligence_state_projection\n\nOCR_010_BUILD_ID="OCR-010"\nOCR_010_REVISION="OCR_010_MARKET_AWARE_CONTINUOUS_REASONING_GATE_V1"\n\n@dataclass(frozen=True)\nclass OCR010Certification:\n    builds:tuple[str,...]\n    capability:str\n    next_capability:str\n    certified:bool=True\n\ndef certify_ocr_006_through_010():\n    if not all((verify_ocr_006_canonical_market_identity_recovery(),verify_ocr_007_umd_market_context_join(),\n                verify_ocr_008_continuous_scientific_reasoning_invocation(),verify_ocr_009_intelligence_state_projection())):\n        raise RuntimeError("OCR-006 through OCR-010 certification failed")\n    return OCR010Certification(tuple("OCR-%03d"%i for i in range(6,11)),\n        "market_aware_live_observation_to_frozen_osr_to_ois_projection",\n        "continuous_reasoning_cursor_state_and_oracle_live_runtime_binding",True)\n\ndef verify_ocr_010_market_aware_continuous_reasoning_capability_gate():\n    c=certify_ocr_006_through_010()\n    return c.certified and len(c.builds)==5\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_010_capability_gate import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_010_market_aware_continuous_reasoning_capability_gate())\n    def test_five(self):self.assertEqual(len(certify_ocr_006_through_010().builds),5)\nif __name__=="__main__":\n    print("="*72);print(" OCR-010 CERTIFICATION TEST");print(" MARKET-AWARE CONTINUOUS REASONING CAPABILITY GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OCR-006 through OCR-010 market-aware live reasoning certified")\n    print("[PASS] Next capability: reasoning cursor/state + Oracle Live Runtime binding")\n    print("[DONE] OCR-010 CERTIFIED")\n'
EXTRA_1='from pathlib import Path\nfrom qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations\nfrom qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import recover_batch_market_identities\nfrom qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import join_rows_to_umd_context\nfrom qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations\nfrom qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import project_reasoning_results\n\nif __name__=="__main__":\n    print("="*72);print(" OCR-010 PHYSICAL MARKET-AWARE LIVE REASONING VERIFICATION");print("="*72)\n    result=read_latest_canonical_observations(Path.cwd(),limit=25)\n    identities=recover_batch_market_identities(result.rows)\n    resolved=tuple(x for x in identities if x.recovered)\n    print(f"[POSTGRESQL] rows={len(result.rows)} read_only={result.read_only}")\n    print(f"[IDENTITY] resolved={len(resolved)} unresolved={len(identities)-len(resolved)} unique_markets={len(set(x.market_ticker for x in resolved))}")\n    aware=join_rows_to_umd_context(result.rows)\n    if not aware:raise SystemExit("[FAIL] No market identities recovered from live observations")\n    reasoning=reason_over_market_aware_observations(aware)\n    print(f"[OSR] markets_reasoned={len(reasoning)}")\n    for r in reasoning[:10]:\n        s=r.osr_state\n        print(f"[OSR] market={r.market_ticker} state={s.reasoning_state} support={s.support:.3f} confidence={s.confidence:.3f} contradiction={s.contradiction:.3f} abstain={s.abstain}")\n    projections=project_reasoning_results(reasoning)\n    print(f"[OIS] read_only_projections={len(projections)}")\n    if not projections:raise SystemExit("[FAIL] No OIS projections produced")\n    print("[PASS] Real PostgreSQL observations recovered market identity")\n    print("[PASS] Market-aware observations invoked frozen OSR-028/029")\n    print("[PASS] Scientific reasoning projected through frozen OIS-002 read-only boundary")\n    print("[DONE] OCR-010 PHYSICAL MARKET-AWARE LIVE REASONING VERIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection')
        if getattr(m,'verify_ocr_009_intelligence_state_projection')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_ocr_010_physical_market_aware_live_reasoning_verification.py');backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_ocr_010_physical_market_aware_live_reasoning_verification.py',EXTRA_1)

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
