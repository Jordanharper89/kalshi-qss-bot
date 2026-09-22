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

BUILD_ID='OCR-006'
TITLE='CANONICAL MARKET IDENTITY RECOVERY'
REVISION='OCR_006_PRODUCTION_V1'
MODULE=PACKAGE/'ocr_006_market_identity_recovery.py'
TEST=ROOT/'test_ocr_006_canonical_market_identity_recovery.py'
EXPORTS=('OCR_006_BUILD_ID', 'OCR_006_REVISION', 'RecoveredMarketIdentity', 'recover_market_identity', 'recover_batch_market_identities', 'verify_ocr_006_canonical_market_identity_recovery')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nimport json,re\n\nOCR_006_BUILD_ID="OCR-006"\nOCR_006_REVISION="OCR_006_CANONICAL_MARKET_IDENTITY_RECOVERY_V1"\nKALSHI_RE=re.compile(r"\\bKX[A-Z0-9][A-Z0-9\\-]*\\b",re.I)\n\n@dataclass(frozen=True)\nclass RecoveredMarketIdentity:\n    observation_id:str\n    market_ticker:str\n    venue:str\n    recovery_path:str\n    recovered:bool=True\n\ndef _json_or_value(v):\n    if isinstance(v,str):\n        s=v.strip()\n        if s and s[0] in "[{\\"":\n            try:return json.loads(s)\n            except Exception:return v\n    return v\n\ndef _walk(value,path="$"):\n    value=_json_or_value(value)\n    if isinstance(value,dict):\n        preferred=("market_ticker","ticker","source_market_id","venue_market_id","market_id")\n        for k in preferred:\n            if k in value:\n                v=str(value[k]).strip()\n                if KALSHI_RE.fullmatch(v):return v,path+"."+k\n        for k in sorted(value):\n            got=_walk(value[k],path+"."+str(k))\n            if got:return got\n    elif isinstance(value,(list,tuple)):\n        for i,v in enumerate(value):\n            got=_walk(v,f"{path}[{i}]")\n            if got:return got\n    elif isinstance(value,str):\n        m=KALSHI_RE.search(value)\n        if m:return m.group(0),path\n    return None\n\ndef recover_market_identity(row):\n    row=dict(row)\n    oid=str(row.get("observation_id") or row.get("id") or "").strip()\n    if not oid:raise ValueError("observation_id required")\n    got=_walk(row)\n    if not got:return RecoveredMarketIdentity(oid,"","kalshi","unresolved",False)\n    ticker,path=got\n    return RecoveredMarketIdentity(oid,ticker.upper(),"kalshi",path,True)\n\ndef recover_batch_market_identities(rows):\n    return tuple(recover_market_identity(r) for r in rows)\n\ndef verify_ocr_006_canonical_market_identity_recovery():\n    x=recover_market_identity({"observation_id":"o","payload":{"msg":{"market_ticker":"KXBTC15M-TEST"}}})\n    return x.recovered and x.market_ticker=="KXBTC15M-TEST"\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_ocr_006_canonical_market_identity_recovery())\n    def test_nested_json(self):\n        x=recover_market_identity({"observation_id":"o","payload":"{\\"msg\\":{\\"ticker\\":\\"KXTEST-1\\"}}"})\n        self.assertEqual(x.market_ticker,"KXTEST-1")\n    def test_unresolved(self):self.assertFalse(recover_market_identity({"observation_id":"o","payload":{"x":1}}).recovered)\nif __name__=="__main__":\n    print("="*72);print(" OCR-006 CERTIFICATION TEST");print(" CANONICAL MARKET IDENTITY RECOVERY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Nested persisted Kalshi market identity recovery certified");print("[DONE] OCR-006 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_continuous_reasoning.ocr_005_capability_gate')
        if getattr(m,'verify_ocr_005_live_reasoning_intake_activation_capability_gate')() is not True:
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
