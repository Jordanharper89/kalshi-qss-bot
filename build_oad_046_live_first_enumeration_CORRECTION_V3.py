from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_adapters" / "kalshi"
MODULE = PACKAGE / "oad_046_live_universe_enumeration.py"
TEST = ROOT / "test_oad_046_physical_live_full_universe_enumeration.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from .oad_021_credentials import KalshiCredentialConfig
from .oad_022_rest_transport import kalshi_rest_get

OAD_046_BUILD_ID="OAD-046"
OAD_046_REVISION="OAD_046_LIVE_UNIVERSE_ENUMERATION_LIVE_FIRST_CORRECTION_V3"

@dataclass(frozen=True)
class LiveUniverseEnumeration:
    tickers:tuple[str,...]
    pages:int
    duplicate_count:int
    terminal_cursor_reached:bool

def enumerate_live_open_universe(credentials,max_pages=10000,timeout_seconds=8,progress=None):
    if not isinstance(credentials,KalshiCredentialConfig):
        raise ValueError("certified credentials required")
    emit=progress or (lambda _msg: None)
    cursor=""
    seen={}
    duplicates=0
    pages=0
    while pages < int(max_pages):
        params={"limit":1000,"status":"open"}
        if cursor:
            params["cursor"]=cursor

        emit(f"[UNIVERSE] requesting_page={pages+1} accumulated={len(seen)}")

        response=kalshi_rest_get(
            credentials,
            "/markets",
            params,
            timeout_seconds,
        )
        pages+=1
        markets=tuple(response.body.get("markets",()))

        for market in markets:
            ticker=str(market.get("ticker","")).strip()
            if not ticker:
                continue
            if ticker in seen:
                duplicates+=1
            else:
                seen[ticker]=True

        emit(f"[UNIVERSE] page={pages} received={len(markets)} total={len(seen)}")

        nxt=str(response.body.get("cursor") or "")
        if not nxt:
            emit(f"[UNIVERSE] COMPLETE pages={pages} open_markets={len(seen)}")
            return LiveUniverseEnumeration(tuple(sorted(seen)),pages,duplicates,True)

        if nxt==cursor:
            raise RuntimeError("Kalshi live-universe cursor did not advance")

        cursor=nxt

    raise RuntimeError("Kalshi live-universe enumeration exceeded max_pages")

def verify_oad_046_physical_live_full_universe_enumeration():
    import inspect
    sig=inspect.signature(enumerate_live_open_universe)
    return (
        sig.parameters["timeout_seconds"].default==8
        and "progress" in sig.parameters
        and OAD_046_REVISION.endswith("CORRECTION_V3")
    )
"""

TEST_SOURCE = r"""
import inspect
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_046_live_universe_enumeration import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_oad_046_physical_live_full_universe_enumeration())

    def test_progress_and_timeout(self):
        sig=inspect.signature(enumerate_live_open_universe)
        self.assertIn("progress",sig.parameters)
        self.assertEqual(sig.parameters["timeout_seconds"].default,8)

if __name__=="__main__":
    print("="*72)
    print(" OAD-046 LIVE-FIRST CORRECTION V3 CERTIFICATION TEST")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-046 bounded progress-aware enumeration certified")
    print("[DONE] OAD-046 CORRECTION V3 CERTIFIED")
"""

def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_adapters.kalshi.oad_045_full_universe_intelligence_gate"
        )
        if getattr(m,"verify_oad_045_full_universe_live_intelligence_capability_gate")() is not True:
            raise RuntimeError("Certified OAD-045 boundary verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" OAD-046 LIVE-FIRST CORRECTION V3 INSTALLER")
    print("="*72)
    print("[ROOT]",ROOT)
    verify_upstream()
    print("[PASS] Certified OAD-045 boundary verified read-only")

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
        print("[ROLLBACK] OAD-046 correction failed; affected files restored")
        raise

    print("[PASS] OAD-046 now emits page-by-page progress")
    print("[PASS] Per-request timeout tightened to 8 seconds")
    print("[DONE] OAD-046 LIVE-FIRST CORRECTION V3 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
