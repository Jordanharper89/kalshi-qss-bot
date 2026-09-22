from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base / "kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p / "kalshi-qss-bot"]
    seen = set()
    for c in candidates:
        try: c = c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c / "qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_adapters"
KALSHI = PACKAGE / "kalshi"
INIT = KALSHI / "__init__.py"

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text.lstrip("\n"), encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker, module, exports):
    current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block = marker + "\nfrom ." + module + " import (\n"
    block += "".join("    " + x + ",\n" for x in exports)
    block += ")\n"
    write_exact(INIT, current.rstrip() + ("\n\n" if current.strip() else "") + block)

def run_test(path):
    p = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: " + path.name)

BUILD_ID='OAD-009'
TITLE='KALSHI UNIVERSE RECONCILIATION + LIFECYCLE CLASSIFICATION'
REVISION='OAD_009_PRODUCTION_V1'
MODULE=KALSHI / 'oad_009_universe_reconciliation.py'
TEST=ROOT / 'test_oad_009_kalshi_universe_reconciliation_lifecycle.py'
EXPORTS=('OAD_009_BUILD_ID', 'OAD_009_REVISION', 'KalshiMarketLifecycleClass', 'KalshiUniverseReconciliation', 'classify_market', 'reconcile_universe', 'build_oad_009_certification_manifest', 'verify_oad_009_kalshi_universe_reconciliation_lifecycle')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType
from .oad_008_full_universe_discovery import KalshiUniverseSnapshot

OAD_009_BUILD_ID="OAD-009"
OAD_009_REVISION="OAD_009_KALSHI_UNIVERSE_RECONCILIATION_LIFECYCLE_V1"

@dataclass(frozen=True)
class KalshiMarketLifecycleClass:
    ticker:str
    raw_status:str
    lifecycle_class:str
    high_speed_eligible:bool
    surveillance_eligible:bool
    terminal:bool

@dataclass(frozen=True)
class KalshiUniverseReconciliation:
    added:tuple[str,...]
    removed:tuple[str,...]
    changed:tuple[str,...]
    active_fast_lane:tuple[str,...]
    broad_surveillance:tuple[str,...]
    terminal_markets:tuple[str,...]

def classify_market(m):
    s=m.status.lower()
    if s in ("active","open"): return KalshiMarketLifecycleClass(m.ticker,s,"LIVE",True,True,False)
    if s in ("inactive","paused"): return KalshiMarketLifecycleClass(m.ticker,s,"PAUSED",False,True,False)
    if s in ("initialized","unopened"): return KalshiMarketLifecycleClass(m.ticker,s,"PREOPEN",False,True,False)
    if s in ("closed","determined","disputed","amended"): return KalshiMarketLifecycleClass(m.ticker,s,"POST_CLOSE",False,True,False)
    if s in ("finalized","settled"): return KalshiMarketLifecycleClass(m.ticker,s,"TERMINAL",False,False,True)
    return KalshiMarketLifecycleClass(m.ticker,s,"UNKNOWN",False,True,False)

def reconcile_universe(previous,current):
    if not isinstance(previous,KalshiUniverseSnapshot) or not isinstance(current,KalshiUniverseSnapshot):
        raise ValueError("certified universe snapshots required")
    a={m.ticker:m for m in previous.markets}; b={m.ticker:m for m in current.markets}
    added=tuple(sorted(set(b)-set(a))); removed=tuple(sorted(set(a)-set(b)))
    changed=tuple(sorted(k for k in set(a)&set(b) if a[k]!=b[k]))
    classes=tuple(classify_market(m) for m in current.markets)
    fast=tuple(sorted(x.ticker for x in classes if x.high_speed_eligible))
    broad=tuple(sorted(x.ticker for x in classes if x.surveillance_eligible))
    terminal=tuple(sorted(x.ticker for x in classes if x.terminal))
    return KalshiUniverseReconciliation(added,removed,changed,fast,broad,terminal)

def build_oad_009_certification_manifest():
    return MappingProxyType({"build_id":OAD_009_BUILD_ID,"revision":OAD_009_REVISION,
        "two_speed_classification":True,"terminal_markets_excluded_from_live_surveillance":True})

def verify_oad_009_kalshi_universe_reconciliation_lifecycle():
    from .oad_008_full_universe_discovery import build_full_universe_snapshot
    p=build_full_universe_snapshot(({"markets":[{"ticker":"A","event_ticker":"E","status":"active"}],"cursor":""},))
    c=build_full_universe_snapshot(({"markets":[{"ticker":"A","event_ticker":"E","status":"finalized"},{"ticker":"B","event_ticker":"E","status":"active"}],"cursor":""},))
    r=reconcile_universe(p,c)
    return r.added==("B",) and r.active_fast_lane==("B",) and r.terminal_markets==("A",)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_008_full_universe_discovery import build_full_universe_snapshot
from qseries_v2.oracle_adapters.kalshi.oad_009_universe_reconciliation import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_009_kalshi_universe_reconciliation_lifecycle())
    def test_paused_surveillance(self):
        s=build_full_universe_snapshot(({"markets":[{"ticker":"A","event_ticker":"E","status":"inactive"}],"cursor":""},))
        r=reconcile_universe(s,s); self.assertEqual(r.broad_surveillance,("A",)); self.assertEqual(r.active_fast_lane,())
    def test_terminal_excluded(self):
        s=build_full_universe_snapshot(({"markets":[{"ticker":"A","event_ticker":"E","status":"finalized"}],"cursor":""},))
        r=reconcile_universe(s,s); self.assertEqual(r.broad_surveillance,()); self.assertEqual(r.terminal_markets,("A",))
if __name__=="__main__":
    print("="*72);print(" OAD-009 CERTIFICATION TEST");print(" KALSHI UNIVERSE RECONCILIATION + LIFECYCLE CLASSIFICATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi two-speed universe lifecycle classification certified");print("[DONE] OAD-009 CERTIFIED")
"""

def verify_upstream():
    p=KALSHI / "oad_008_full_universe_discovery.py"
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_008_full_universe_discovery')
        if getattr(m,'verify_oad_008_kalshi_full_universe_discovery')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72); print(" "+BUILD_ID+" INSTALLER"); print(" "+TITLE); print("="*72)
    print("[BOOT] Revision: "+REVISION); print("[ROOT] "+str(ROOT))
    verify_upstream(); print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        KALSHI.mkdir(parents=True,exist_ok=True)
        if not INIT.exists():
            write_exact(INIT,'"""Kalshi read-only Oracle adapter implementation."""\n')
        write_exact(MODULE,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE)
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
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),
              TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__": main()
