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

BUILD_ID='OCR-007'
TITLE='UMD MARKET CONTEXT JOIN'
REVISION='OCR_007_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_007_umd_context_join.py'
TEST=ROOT/'test_ocr_007_umd_market_context_join.py'
EXPORTS=('OCR_007_BUILD_ID', 'OCR_007_REVISION', 'MarketAwareObservation', 'build_umd_context_for_recovered_identity', 'join_rows_to_umd_context', 'verify_ocr_007_umd_market_context_join')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_continuous_intake.oci_007_umd_context_binding import UMDMarketContext\n\nOCR_007_BUILD_ID="OCR-007"\nOCR_007_REVISION="OCR_007_UMD_MARKET_CONTEXT_JOIN_V1"\n\n@dataclass(frozen=True)\nclass MarketAwareObservation:\n    observation_id:str\n    market_ticker:str\n    context:UMDMarketContext\n    source_row:dict\n    umd_read_only:bool=True\n\ndef build_umd_context_for_recovered_identity(identity):\n    if not identity.recovered or not identity.market_ticker:raise ValueError("recovered market identity required")\n    # Frozen OCI-007 public context contract. The venue ticker remains the canonical\n    # runtime identity until a richer UMD registry record is available to this process.\n    return UMDMarketContext(identity.market_ticker,"kalshi",identity.market_ticker,(),(identity.market_ticker,))\n\ndef join_rows_to_umd_context(rows):\n    from .ocr_006_market_identity_recovery import recover_market_identity\n    out=[]\n    for row in rows:\n        identity=recover_market_identity(row)\n        if not identity.recovered:continue\n        out.append(MarketAwareObservation(identity.observation_id,identity.market_ticker,\n                   build_umd_context_for_recovered_identity(identity),dict(row),True))\n    return tuple(out)\n\ndef verify_ocr_007_umd_market_context_join():\n    x=join_rows_to_umd_context(({"observation_id":"o","payload":{"ticker":"KXTEST-1"}},))\n    return len(x)==1 and x[0].context.venue=="kalshi" and x[0].umd_read_only\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_007_umd_market_context_join())\n    def test_read_only(self):self.assertTrue(join_rows_to_umd_context(({"observation_id":"o","ticker":"KXTEST"},))[0].umd_read_only)\nif __name__=="__main__":\n    print("="*72);print(" OCR-007 CERTIFICATION TEST");print(" UMD MARKET CONTEXT JOIN");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Frozen OCI-007 UMD context contract joined to recovered markets");print("[DONE] OCR-007 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery')
        if getattr(m,'verify_ocr_006_canonical_market_identity_recovery')() is not True:
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
