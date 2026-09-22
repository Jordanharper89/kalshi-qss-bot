from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"
def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)
def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-046'
TITLE='PHYSICAL LIVE FULL-UNIVERSE ENUMERATION'
REVISION='OAD_046_PRODUCTION_V1'
MODULE=PACKAGE/'oad_046_live_universe_enumeration.py'
TEST=ROOT/'test_oad_046_physical_live_full_universe_enumeration.py'
EXPORTS=('OAD_046_BUILD_ID', 'OAD_046_REVISION', 'LiveUniverseEnumeration', 'enumerate_live_open_universe', 'verify_oad_046_physical_live_full_universe_enumeration')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_021_credentials import KalshiCredentialConfig\nfrom .oad_022_rest_transport import kalshi_rest_get\nOAD_046_BUILD_ID="OAD-046"\nOAD_046_REVISION="OAD_046_PHYSICAL_LIVE_FULL_UNIVERSE_ENUMERATION_V1"\n@dataclass(frozen=True)\nclass LiveUniverseEnumeration:\n    tickers:tuple[str,...]; pages:int; duplicate_count:int; terminal_cursor_reached:bool\ndef enumerate_live_open_universe(credentials,max_pages=10000,timeout_seconds=15):\n    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")\n    cursor=""; seen={}; dup=0; pages=0\n    for _ in range(int(max_pages)):\n        params={"limit":1000,"status":"open"}\n        if cursor: params["cursor"]=cursor\n        r=kalshi_rest_get(credentials,"/markets",params,timeout_seconds); pages+=1\n        for market in r.body.get("markets",()):\n            ticker=str(market.get("ticker","")).strip()\n            if not ticker: continue\n            if ticker in seen: dup+=1\n            else: seen[ticker]=True\n        nxt=str(r.body.get("cursor") or "")\n        if not nxt: return LiveUniverseEnumeration(tuple(sorted(seen)),pages,dup,True)\n        if nxt==cursor: raise RuntimeError("cursor did not advance")\n        cursor=nxt\n    raise RuntimeError("enumeration exceeded max_pages")\ndef verify_oad_046_physical_live_full_universe_enumeration(): return OAD_046_REVISION.endswith("_V1")\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_046_live_universe_enumeration import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_046_physical_live_full_universe_enumeration())\nif __name__=="__main__":\n    print("="*72);print(" OAD-046 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Physical live full-universe enumeration implementation certified");print("[DONE] OAD-046 CERTIFIED")\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_045_full_universe_intelligence_gate')
        if getattr(m,'verify_oad_045_full_universe_live_intelligence_capability_gate')() is not True: raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
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
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            v=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if v() is not True: raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)));print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name);print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
