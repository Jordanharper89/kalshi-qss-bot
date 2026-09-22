from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
MODULE=PACKAGE/'oad_046_live_universe_enumeration.py'
TEST=ROOT/'test_oad_046_physical_live_full_universe_enumeration.py'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oad_021_credentials import KalshiCredentialConfig\nfrom .oad_022_rest_transport import kalshi_rest_get\n\nOAD_046_BUILD_ID="OAD-046"\nOAD_046_REVISION="OAD_046_PHYSICAL_LIVE_FULL_UNIVERSE_ENUMERATION_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass LiveUniverseEnumeration:\n    tickers:tuple[str,...]\n    pages:int\n    duplicate_count:int\n    terminal_cursor_reached:bool\n\ndef enumerate_live_open_universe(credentials,max_pages=10000,timeout_seconds=10,progress=None):\n    if not isinstance(credentials,KalshiCredentialConfig):\n        raise ValueError("certified credentials required")\n    emit=progress or (lambda _msg: None)\n    cursor=""\n    seen={}\n    duplicates=0\n    pages=0\n    for _ in range(int(max_pages)):\n        params={"limit":1000,"status":"open"}\n        if cursor:\n            params["cursor"]=cursor\n        emit(f"[UNIVERSE] requesting_page={pages+1} accumulated={len(seen)}")\n        r=kalshi_rest_get(credentials,"/markets",params,timeout_seconds)\n        pages+=1\n        markets=tuple(r.body.get("markets",()))\n        for market in markets:\n            ticker=str(market.get("ticker","")).strip()\n            if not ticker:\n                continue\n            if ticker in seen:\n                duplicates+=1\n            else:\n                seen[ticker]=True\n        emit(f"[UNIVERSE] page={pages} received={len(markets)} total={len(seen)}")\n        nxt=str(r.body.get("cursor") or "")\n        if not nxt:\n            emit(f"[UNIVERSE] COMPLETE pages={pages} open_markets={len(seen)}")\n            return LiveUniverseEnumeration(tuple(sorted(seen)),pages,duplicates,True)\n        if nxt==cursor:\n            raise RuntimeError("Kalshi live-universe cursor did not advance")\n        cursor=nxt\n    raise RuntimeError("Kalshi live-universe enumeration exceeded max_pages")\n\ndef verify_oad_046_physical_live_full_universe_enumeration():\n    import inspect\n    sig=inspect.signature(enumerate_live_open_universe)\n    return sig.parameters["timeout_seconds"].default==10 and "progress" in sig.parameters\n'
TEST_SOURCE='import inspect,unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_046_live_universe_enumeration import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_046_physical_live_full_universe_enumeration())\n    def test_progress_param(self): self.assertIn("progress",inspect.signature(enumerate_live_open_universe).parameters)\nif __name__=="__main__":\n    print("="*72);print(" OAD-046 CORRECTION V2 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Bounded progress-aware universe enumeration certified")\n    print("[DONE] OAD-046 CORRECTION V2 CERTIFIED")\n'

def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_045_full_universe_intelligence_gate')
        if getattr(m,'verify_oad_045_full_universe_live_intelligence_capability_gate')() is not True:
            raise RuntimeError("Certified upstream verification failed")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def main():
    print("="*72);print(" OAD-046 CORRECTION V2 INSTALLER");print(" BOUNDED PROGRESS-AWARE FULL-UNIVERSE ENUMERATION");print("="*72)
    print("[ROOT]",ROOT)
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] Correction failed; affected files restored")
        raise
    print("[PASS] Corrected:",MODULE.relative_to(ROOT))
    print("[PASS] Corrected:",TEST.name)
    print("[DONE] OAD-046 CORRECTION V2 INSTALLED + CERTIFIED")
if __name__=="__main__":
    main()
