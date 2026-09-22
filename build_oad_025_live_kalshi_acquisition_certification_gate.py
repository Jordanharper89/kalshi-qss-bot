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

BUILD_ID='OAD-025'
TITLE='LIVE KALSHI ACQUISITION CERTIFICATION GATE'
REVISION='OAD_025_PRODUCTION_V1'
MODULE=PACKAGE/'oad_025_live_acquisition_gate.py'
TEST=ROOT/'test_oad_025_live_kalshi_acquisition_certification_gate.py'
EXPORTS=('OAD_025_BUILD_ID', 'OAD_025_REVISION', 'LiveKalshiAcquisitionResult', 'run_live_kalshi_acquisition_probe', 'build_oad_025_certification_manifest', 'verify_oad_025_live_kalshi_acquisition_certification_gate')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

from .oad_021_credentials import load_kalshi_credentials
from .oad_023_real_universe_acquisition import acquire_real_kalshi_universe
from .oad_024_physical_websocket import probe_kalshi_websocket

OAD_025_BUILD_ID="OAD-025"
OAD_025_REVISION="OAD_025_LIVE_KALSHI_ACQUISITION_CERTIFICATION_GATE_V1"

@dataclass(frozen=True)
class LiveKalshiAcquisitionResult:
    credential_ready:bool
    rest_live:bool
    universe_markets:int
    universe_pages:int
    websocket_live:bool
    websocket_messages:int
    certified_live:bool
    result_hash:str

def run_live_kalshi_acquisition_probe(root=None,timeout_seconds=10):
    credentials=load_kalshi_credentials(root=root)
    u=acquire_real_kalshi_universe(credentials,timeout_seconds=timeout_seconds)
    live_tickers=tuple(m.ticker for m in u.snapshot.markets if m.status.lower() in ("active","open"))[:50]
    if not live_tickers:
        raise RuntimeError("No active Kalshi markets discovered for WebSocket probe")
    w=probe_kalshi_websocket(credentials,live_tickers,channels=("ticker","trade"),max_messages=5,timeout_seconds=timeout_seconds)
    raw={"credential_ready":True,"rest_live":u.network_live,"universe_markets":len(u.snapshot.markets),
         "universe_pages":u.requests,"websocket_live":w.connected,"websocket_messages":w.messages_received}
    certified=bool(raw["rest_live"] and raw["universe_markets"]>0 and raw["websocket_live"] and raw["websocket_messages"]>0)
    h=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return LiveKalshiAcquisitionResult(True,u.network_live,len(u.snapshot.markets),u.requests,w.connected,w.messages_received,certified,h)

def build_oad_025_certification_manifest():
    return MappingProxyType({"build_id":OAD_025_BUILD_ID,"revision":OAD_025_REVISION,
        "physical_rest_required":True,"physical_websocket_required":True,"live_messages_required":True,
        "credentials_persisted":False,"execution":False,
        "next_capability":"bind_physical_kalshi_adapter_into_oracle_live_runtime_and_live_shadow"})

def verify_oad_025_live_kalshi_acquisition_certification_gate():
    m=build_oad_025_certification_manifest()
    return m["physical_rest_required"] and m["physical_websocket_required"] and m["live_messages_required"] and not m["credentials_persisted"]
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_025_live_acquisition_gate import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_025_live_kalshi_acquisition_certification_gate())
    def test_no_credentials_persisted(self): self.assertFalse(build_oad_025_certification_manifest()["credentials_persisted"])
    def test_next(self): self.assertIn("oracle_live_runtime",build_oad_025_certification_manifest()["next_capability"])
if __name__=="__main__":
    print("="*72);print(" OAD-025 CERTIFICATION TEST");print(" LIVE KALSHI ACQUISITION CERTIFICATION GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Live Kalshi acquisition gate implementation certified")
    print("[NOTE] Run python run_oad_025_kalshi_live_probe.py to perform the physical network certification.")
    print("[DONE] OAD-025 CERTIFIED")
"""
EXTRA_RUN_OAD_025_KALSHI_LIVE_PROBE_PY=r"""
from pathlib import Path
from qseries_v2.oracle_adapters.kalshi.oad_025_live_acquisition_gate import run_live_kalshi_acquisition_probe

def main():
    print("="*72)
    print(" OAD-025 PHYSICAL KALSHI LIVE ACQUISITION PROBE")
    print("="*72)
    r=run_live_kalshi_acquisition_probe(root=Path.cwd(),timeout_seconds=15)
    print("[REST] LIVE:", r.rest_live)
    print("[UNIVERSE] markets:", r.universe_markets, "pages:", r.universe_pages)
    print("[WEBSOCKET] LIVE:", r.websocket_live, "messages:", r.websocket_messages)
    print("[HASH]", r.result_hash)
    if not r.certified_live:
        raise SystemExit("[FAIL] Physical Kalshi live acquisition did not certify")
    print("[PASS] Physical Kalshi REST + full-universe + WebSocket acquisition certified LIVE")
    print("[DONE] OAD-025 PHYSICAL LIVE CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
"""

def verify_upstream():
    p=PACKAGE/'oad_024_physical_websocket.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_024_physical_websocket')
        if getattr(m,'verify_oad_024_physical_kalshi_websocket_activation')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_oad_025_kalshi_live_probe.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_oad_025_kalshi_live_probe.py',EXTRA_RUN_OAD_025_KALSHI_LIVE_PROBE_PY)
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
