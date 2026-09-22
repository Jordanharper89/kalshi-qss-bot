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

BUILD_ID='OAD-008'
TITLE='KALSHI FULL-UNIVERSE MARKET DISCOVERY'
REVISION='OAD_008_PRODUCTION_V1'
MODULE=KALSHI / 'oad_008_full_universe_discovery.py'
TEST=ROOT / 'test_oad_008_kalshi_full_universe_discovery.py'
EXPORTS=('OAD_008_BUILD_ID', 'OAD_008_REVISION', 'KALSHI_MARKET_FILTERS', 'KalshiMarketRecord', 'KalshiUniverseSnapshot', 'build_markets_page_request', 'normalize_market', 'build_full_universe_snapshot', 'build_oad_008_certification_manifest', 'verify_oad_008_kalshi_full_universe_discovery')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OAD_008_BUILD_ID="OAD-008"
OAD_008_REVISION="OAD_008_KALSHI_FULL_UNIVERSE_DISCOVERY_V1"
KALSHI_MARKET_FILTERS=("unopened","open","paused","closed","settled")

@dataclass(frozen=True)
class KalshiMarketRecord:
    ticker:str
    event_ticker:str
    status:str
    title:str
    updated_time:str
    exchange_index:int

@dataclass(frozen=True)
class KalshiUniverseSnapshot:
    markets:tuple[KalshiMarketRecord,...]
    statuses:tuple[str,...]
    page_count:int
    complete:bool
    snapshot_hash:str

def build_markets_page_request(cursor=""):
    q={"limit":1000}
    if cursor: q["cursor"]=cursor
    return MappingProxyType(q)

def normalize_market(raw):
    ticker=str(raw.get("ticker","")).strip()
    event=str(raw.get("event_ticker","")).strip()
    status=str(raw.get("status","")).strip().lower()
    if not ticker or not event or not status: raise ValueError("ticker/event_ticker/status required")
    return KalshiMarketRecord(ticker,event,status,str(raw.get("title","")),
                              str(raw.get("updated_time","")),int(raw.get("exchange_index",0)))

def build_full_universe_snapshot(pages):
    records={}
    page_count=0
    terminal=False
    for page in pages:
        page_count+=1
        for raw in page.get("markets",()):
            m=normalize_market(raw)
            if m.ticker in records and records[m.ticker]!=m: raise ValueError("conflicting duplicate market")
            records[m.ticker]=m
        terminal=not bool(page.get("cursor",""))
    if not page_count or not terminal: raise ValueError("complete cursor pagination required")
    markets=tuple(sorted(records.values(),key=lambda x:x.ticker))
    statuses=tuple(sorted({m.status for m in markets}))
    payload=[m.__dict__ for m in markets]
    h=sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiUniverseSnapshot(markets,statuses,page_count,True,h)

def build_oad_008_certification_manifest():
    return MappingProxyType({"build_id":OAD_008_BUILD_ID,"revision":OAD_008_REVISION,
        "page_limit":1000,"cursor_pagination":True,"status_filter_omitted_for_full_universe":True})

def verify_oad_008_kalshi_full_universe_discovery():
    pages=({"markets":[{"ticker":"B","event_ticker":"E","status":"active"},{"ticker":"A","event_ticker":"E","status":"initialized"}],"cursor":"NEXT"},
           {"markets":[{"ticker":"C","event_ticker":"E2","status":"finalized"}],"cursor":""})
    s=build_full_universe_snapshot(pages)
    return s.complete and s.page_count==2 and tuple(x.ticker for x in s.markets)==("A","B","C") and build_markets_page_request()["limit"]==1000
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_008_full_universe_discovery import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_008_kalshi_full_universe_discovery())
    def test_limit(self): self.assertEqual(build_markets_page_request()["limit"],1000)
    def test_incomplete_rejected(self):
        with self.assertRaises(ValueError): build_full_universe_snapshot(({"markets":[],"cursor":"NEXT"},))
    def test_deterministic(self):
        p=({"markets":[{"ticker":"A","event_ticker":"E","status":"active"}],"cursor":""},)
        self.assertEqual(build_full_universe_snapshot(p).snapshot_hash,build_full_universe_snapshot(p).snapshot_hash)
if __name__=="__main__":
    print("="*72);print(" OAD-008 CERTIFICATION TEST");print(" KALSHI FULL-UNIVERSE MARKET DISCOVERY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi cursor-paginated full-universe discovery certified");print("[DONE] OAD-008 CERTIFIED")
"""

def verify_upstream():
    p=KALSHI / "oad_007_transport_auth.py"
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_007_transport_auth')
        if getattr(m,'verify_oad_007_kalshi_transport_auth_boundary')() is not True:
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
