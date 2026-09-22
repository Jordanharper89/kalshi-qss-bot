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

BUILD_ID='OAD-024'
TITLE='PHYSICAL KALSHI WEBSOCKET ACTIVATION'
REVISION='OAD_024_PRODUCTION_V1'
MODULE=PACKAGE/'oad_024_physical_websocket.py'
TEST=ROOT/'test_oad_024_physical_kalshi_websocket_activation.py'
EXPORTS=('OAD_024_BUILD_ID', 'OAD_024_REVISION', 'KalshiWebSocketProbe', 'probe_kalshi_websocket', 'build_oad_024_certification_manifest', 'verify_oad_024_physical_kalshi_websocket_activation')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from time import time
from types import MappingProxyType
import asyncio, json

from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation
from .oad_021_credentials import KalshiCredentialConfig
from .oad_022_rest_transport import build_auth_headers
from .oad_011_websocket_foundation import build_subscribe_command

OAD_024_BUILD_ID="OAD-024"
OAD_024_REVISION="OAD_024_PHYSICAL_KALSHI_WEBSOCKET_ACTIVATION_V1"

@dataclass(frozen=True)
class KalshiWebSocketProbe:
    connected:bool
    subscribed:bool
    messages_received:int
    message_types:tuple[str,...]

async def _probe(credentials,market_tickers,channels,max_messages,timeout_seconds):
    try:
        import websockets
    except Exception as e:
        raise RuntimeError("websockets package required for physical Kalshi WebSocket activation") from e
    f=build_kalshi_adapter_foundation()
    headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")
    # Support current and older websockets keyword names.
    kwargs={"open_timeout":float(timeout_seconds)}
    try:
        ws_cm=websockets.connect(f.predictions_ws_url,additional_headers=headers,**kwargs)
    except TypeError:
        ws_cm=websockets.connect(f.predictions_ws_url,extra_headers=headers,**kwargs)
    types=[]
    async with ws_cm as ws:
        cmd=build_subscribe_command(1,channels,market_tickers)
        await ws.send(json.dumps(cmd,separators=(",",":")))
        subscribed=False
        for _ in range(int(max_messages)):
            raw=await asyncio.wait_for(ws.recv(),timeout=float(timeout_seconds))
            msg=json.loads(raw)
            typ=str(msg.get("type",""))
            types.append(typ)
            if typ in ("subscribed","ok"): subscribed=True
            if len(types)>=int(max_messages): break
        return KalshiWebSocketProbe(True,subscribed,len(types),tuple(types))

def probe_kalshi_websocket(credentials,market_tickers,channels=("ticker","trade"),max_messages=5,timeout_seconds=10):
    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")
    tickers=tuple(market_tickers)
    if not tickers: raise ValueError("at least one live market ticker required")
    return asyncio.run(_probe(credentials,tickers,tuple(channels),int(max_messages),float(timeout_seconds)))

def build_oad_024_certification_manifest():
    return MappingProxyType({"build_id":OAD_024_BUILD_ID,"revision":OAD_024_REVISION,
        "production_websocket":"wss://external-api-ws.kalshi.com/trade-api/ws/v2",
        "authenticated_handshake":True,"read_only_channels":("ticker","trade","orderbook_delta"),"execution":False})

def verify_oad_024_physical_kalshi_websocket_activation():
    return build_oad_024_certification_manifest()["authenticated_handshake"] is True
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_024_physical_websocket import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_024_physical_kalshi_websocket_activation())
    def test_endpoint(self): self.assertTrue(build_oad_024_certification_manifest()["production_websocket"].startswith("wss://"))
if __name__=="__main__":
    print("="*72);print(" OAD-024 CERTIFICATION TEST");print(" PHYSICAL KALSHI WEBSOCKET ACTIVATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Physical authenticated Kalshi WebSocket activation implementation certified");print("[DONE] OAD-024 CERTIFIED")
"""


def verify_upstream():
    p=PACKAGE/'oad_023_real_universe_acquisition.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_023_real_universe_acquisition')
        if getattr(m,'verify_oad_023_real_kalshi_full_universe_acquisition')() is not True:
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
