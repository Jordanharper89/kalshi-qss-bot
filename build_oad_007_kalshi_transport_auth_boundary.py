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

BUILD_ID='OAD-007'
TITLE='KALSHI TRANSPORT + AUTHENTICATION BOUNDARY'
REVISION='OAD_007_PRODUCTION_V1'
MODULE=KALSHI / 'oad_007_transport_auth.py'
TEST=ROOT / 'test_oad_007_kalshi_transport_auth_boundary.py'
EXPORTS=('OAD_007_BUILD_ID', 'OAD_007_REVISION', 'KalshiTransportAuthBoundary', 'signing_message', 'build_kalshi_transport_auth_boundary', 'build_oad_007_certification_manifest', 'verify_oad_007_kalshi_transport_auth_boundary')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType
from urllib.parse import urlsplit
from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation

OAD_007_BUILD_ID="OAD-007"
OAD_007_REVISION="OAD_007_KALSHI_TRANSPORT_AUTH_BOUNDARY_V1"

@dataclass(frozen=True)
class KalshiTransportAuthBoundary:
    rest_base:str
    websocket_url:str
    websocket_handshake_path:str
    signing_algorithm:str
    required_headers:tuple[str,...]
    private_key_material_stored:bool
    order_methods_allowed:bool

def signing_message(timestamp_ms,method,path):
    if int(timestamp_ms)<0: raise ValueError("non-negative timestamp required")
    method=str(method).upper()
    clean=urlsplit(path).path
    if not clean.startswith("/"): raise ValueError("absolute request path required")
    return str(int(timestamp_ms))+method+clean

def build_kalshi_transport_auth_boundary():
    f=build_kalshi_adapter_foundation()
    return KalshiTransportAuthBoundary(
        f.predictions_rest_base,f.predictions_ws_url,"/trade-api/ws/v2",
        "RSA-PSS-SHA256",
        ("KALSHI-ACCESS-KEY","KALSHI-ACCESS-TIMESTAMP","KALSHI-ACCESS-SIGNATURE"),
        False,False
    )

def build_oad_007_certification_manifest():
    x=build_kalshi_transport_auth_boundary()
    return MappingProxyType({"build_id":OAD_007_BUILD_ID,"revision":OAD_007_REVISION,
        "signing_algorithm":x.signing_algorithm,"private_key_material_stored":False,"order_methods_allowed":False})

def verify_oad_007_kalshi_transport_auth_boundary():
    x=build_kalshi_transport_auth_boundary()
    msg=signing_message(123,"get","/trade-api/v2/markets?limit=1000")
    return msg=="123GET/trade-api/v2/markets" and len(x.required_headers)==3 and not x.private_key_material_stored and not x.order_methods_allowed
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_007_transport_auth import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_007_kalshi_transport_auth_boundary())
    def test_query_stripped(self): self.assertEqual(signing_message(5,"GET","/trade-api/v2/markets?limit=1"),"5GET/trade-api/v2/markets")
    def test_no_orders(self): self.assertFalse(build_kalshi_transport_auth_boundary().order_methods_allowed)
if __name__=="__main__":
    print("="*72);print(" OAD-007 CERTIFICATION TEST");print(" KALSHI TRANSPORT + AUTHENTICATION BOUNDARY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi REST/WebSocket authentication boundary certified read-only");print("[DONE] OAD-007 CERTIFIED")
"""

def verify_upstream():
    p=KALSHI / "oad_006_kalshi_foundation.py"
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_006_kalshi_foundation')
        if getattr(m,'verify_oad_006_kalshi_adapter_foundation')() is not True:
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
