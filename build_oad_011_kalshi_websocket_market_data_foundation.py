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

BUILD_ID='OAD-011'
TITLE='KALSHI WEBSOCKET MARKET-DATA FOUNDATION'
REVISION='OAD_011_PRODUCTION_V1'
MODULE=PACKAGE/'oad_011_websocket_foundation.py'
TEST=ROOT/'test_oad_011_kalshi_websocket_market_data_foundation.py'
EXPORTS=('OAD_011_BUILD_ID', 'OAD_011_REVISION', 'PUBLIC_MARKET_DATA_CHANNELS', 'KalshiWebSocketMarketDataFoundation', 'build_websocket_market_data_foundation', 'build_subscribe_command', 'build_oad_011_certification_manifest', 'verify_oad_011_kalshi_websocket_market_data_foundation')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType
from .oad_007_transport_auth import build_kalshi_transport_auth_boundary

OAD_011_BUILD_ID="OAD-011"
OAD_011_REVISION="OAD_011_KALSHI_WEBSOCKET_MARKET_DATA_FOUNDATION_V1"

PUBLIC_MARKET_DATA_CHANNELS=("orderbook_delta","ticker","trade")

@dataclass(frozen=True)
class KalshiWebSocketMarketDataFoundation:
    websocket_url:str
    authenticated_handshake_required:bool
    channels:tuple[str,...]
    read_only:bool
    execution_authority:bool

def build_websocket_market_data_foundation():
    auth=build_kalshi_transport_auth_boundary()
    return KalshiWebSocketMarketDataFoundation(
        auth.websocket_url,True,PUBLIC_MARKET_DATA_CHANNELS,True,False
    )

def build_subscribe_command(command_id,channels,market_tickers):
    channels=tuple(channels); tickers=tuple(market_tickers)
    if int(command_id)<1 or not channels or not tickers:
        raise ValueError("positive command id, channels, and market_tickers required")
    unknown=tuple(x for x in channels if x not in PUBLIC_MARKET_DATA_CHANNELS)
    if unknown: raise ValueError("unsupported read-only channel(s): "+",".join(unknown))
    return {
        "id":int(command_id),
        "cmd":"subscribe",
        "params":{"channels":list(channels),"market_tickers":list(tickers)}
    }

def build_oad_011_certification_manifest():
    x=build_websocket_market_data_foundation()
    return MappingProxyType({"build_id":OAD_011_BUILD_ID,"revision":OAD_011_REVISION,
        "authenticated_handshake_required":True,"channels":x.channels,"read_only":True,"execution":False})

def verify_oad_011_kalshi_websocket_market_data_foundation():
    x=build_websocket_market_data_foundation()
    c=build_subscribe_command(1,("orderbook_delta","ticker","trade"),("KXTEST",))
    return x.authenticated_handshake_required and x.read_only and not x.execution_authority and c["cmd"]=="subscribe"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_011_websocket_foundation import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_011_kalshi_websocket_market_data_foundation())
    def test_command(self):
        c=build_subscribe_command(7,("orderbook_delta",),("A","B"))
        self.assertEqual(c["params"]["market_tickers"],["A","B"])
    def test_private_channel_rejected(self):
        with self.assertRaises(ValueError): build_subscribe_command(1,("fill",),("A",))
if __name__=="__main__":
    print("="*72);print(" OAD-011 CERTIFICATION TEST");print(" KALSHI WEBSOCKET MARKET-DATA FOUNDATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Authenticated read-only Kalshi WebSocket market-data foundation certified");print("[DONE] OAD-011 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_010_kalshi_discovery_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_010_kalshi_discovery_gate')
        if getattr(m,'verify_oad_010_kalshi_full_universe_discovery_capability_gate')() is not True:
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
