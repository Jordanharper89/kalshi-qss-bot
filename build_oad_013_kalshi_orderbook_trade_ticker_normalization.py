from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-013'
TITLE='KALSHI ORDERBOOK / TRADE / TICKER NORMALIZATION'
REVISION='OAD_013_PRODUCTION_V1'
MODULE=PACKAGE/'oad_013_market_data_normalization.py'
TEST=ROOT/'test_oad_013_kalshi_orderbook_trade_ticker_normalization.py'
EXPORTS=('OAD_013_BUILD_ID', 'OAD_013_REVISION', 'NormalizedKalshiMarketData', 'normalize_kalshi_market_data', 'build_oad_013_certification_manifest', 'verify_oad_013_kalshi_orderbook_trade_ticker_normalization')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from qseries_v2.oracle_adapters.oad_003_canonical_event import build_canonical_source_event

OAD_013_BUILD_ID="OAD-013"
OAD_013_REVISION="OAD_013_KALSHI_ORDERBOOK_TRADE_TICKER_NORMALIZATION_V1"

@dataclass(frozen=True)
class NormalizedKalshiMarketData:
    event_type:str
    market_ticker:str
    sid:int
    seq:int
    source_event_ns:int
    canonical_event_hash:str

def _source_ns(raw,receive_ns):
    msg=raw.get("msg") or {}
    if "ts_ms" in msg: return int(msg["ts_ms"])*1_000_000
    if "ts" in msg and isinstance(msg["ts"],(int,float)): return int(msg["ts"])*1_000_000_000
    return int(receive_ns)

def normalize_kalshi_market_data(raw,oracle_receive_ns):
    typ=str(raw.get("type",""))
    if typ not in ("orderbook_snapshot","orderbook_delta","ticker","trade"):
        raise ValueError("unsupported Kalshi market-data event")
    msg=raw.get("msg") or {}
    ticker=str(msg.get("market_ticker") or msg.get("ticker") or "")
    if not ticker: raise ValueError("market ticker required")
    sid=int(raw.get("sid",0)); seq=int(raw.get("seq",0))
    if sid<0 or seq<0: raise ValueError("non-negative sid/seq required")
    src=_source_ns(raw,oracle_receive_ns)
    if src>int(oracle_receive_ns): src=int(oracle_receive_ns)
    canonical=build_canonical_source_event(
        "kalshi_predictions_universal","kalshi",ticker,typ,src,int(oracle_receive_ns),seq,raw
    )
    return NormalizedKalshiMarketData(typ,ticker,sid,seq,src,canonical.envelope_hash)

def build_oad_013_certification_manifest():
    return MappingProxyType({"build_id":OAD_013_BUILD_ID,"revision":OAD_013_REVISION,
        "events":("orderbook_snapshot","orderbook_delta","ticker","trade"),"fixed_point_safe":True,"execution":False})

def verify_oad_013_kalshi_orderbook_trade_ticker_normalization():
    raw={"type":"orderbook_delta","sid":2,"seq":3,"msg":{"market_ticker":"KXTEST","price_dollars":"0.960","delta_fp":"-54.00","side":"yes","ts_ms":100}}
    x=normalize_kalshi_market_data(raw,100_000_001)
    return x.event_type=="orderbook_delta" and x.market_ticker=="KXTEST" and x.seq==3 and len(x.canonical_event_hash)==64
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_013_market_data_normalization import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_013_kalshi_orderbook_trade_ticker_normalization())
    def test_snapshot(self):
        x=normalize_kalshi_market_data({"type":"orderbook_snapshot","sid":1,"seq":1,"msg":{"market_ticker":"A","yes_dollars_fp":[["0.5","1.0"]],"no_dollars_fp":[]}},10)
        self.assertEqual(x.event_type,"orderbook_snapshot")
    def test_bad_type(self):
        with self.assertRaises(ValueError): normalize_kalshi_market_data({"type":"fill","msg":{"market_ticker":"A"}},10)
if __name__=="__main__":
    print("="*72);print(" OAD-013 CERTIFICATION TEST");print(" ORDERBOOK / TRADE / TICKER EVENT NORMALIZATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi public market-data event normalization certified");print("[DONE] OAD-013 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_012_subscription_partitioning.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_012_subscription_partitioning')
        if getattr(m,'verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
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
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
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
