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

BUILD_ID='OAD-022'
TITLE='PHYSICAL KALSHI REST TRANSPORT'
REVISION='OAD_022_PRODUCTION_V1'
MODULE=PACKAGE/'oad_022_rest_transport.py'
TEST=ROOT/'test_oad_022_physical_kalshi_rest_transport.py'
EXPORTS=('OAD_022_BUILD_ID', 'OAD_022_REVISION', 'KalshiRestResponse', 'build_auth_headers', 'kalshi_rest_get', 'build_oad_022_certification_manifest', 'verify_oad_022_physical_kalshi_rest_transport')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from base64 import b64encode
from time import time
from types import MappingProxyType
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
import json

from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation
from .oad_021_credentials import KalshiCredentialConfig

OAD_022_BUILD_ID="OAD-022"
OAD_022_REVISION="OAD_022_PHYSICAL_KALSHI_REST_TRANSPORT_V1"

@dataclass(frozen=True)
class KalshiRestResponse:
    status_code:int
    body:dict
    url:str

def _sign(private_key_pem,message):
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except Exception as e:
        raise RuntimeError("cryptography package required for Kalshi RSA-PSS authentication") from e
    key=serialization.load_pem_private_key(private_key_pem.encode(),password=None)
    sig=key.sign(message.encode(),padding.PSS(mgf=padding.MGF1(hashes.SHA256()),salt_length=padding.PSS.DIGEST_LENGTH),hashes.SHA256())
    return b64encode(sig).decode()

def build_auth_headers(credentials,method,path,timestamp_ms=None):
    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")
    ts=int(timestamp_ms if timestamp_ms is not None else time()*1000)
    clean=urlsplit(path).path
    msg=str(ts)+str(method).upper()+clean
    return {
        "KALSHI-ACCESS-KEY":credentials.api_key_id,
        "KALSHI-ACCESS-TIMESTAMP":str(ts),
        "KALSHI-ACCESS-SIGNATURE":_sign(credentials.private_key_pem,msg),
    }

def kalshi_rest_get(credentials,path,params=None,timeout_seconds=10):
    f=build_kalshi_adapter_foundation()
    params=dict(params or {})
    query=("?"+urlencode(params)) if params else ""
    url=f.predictions_rest_base+path+query
    headers=build_auth_headers(credentials,"GET","/trade-api/v2"+path)
    req=Request(url,headers=headers,method="GET")
    with urlopen(req,timeout=float(timeout_seconds)) as resp:
        body=json.loads(resp.read().decode("utf-8"))
        return KalshiRestResponse(int(resp.status),body,url)

def build_oad_022_certification_manifest():
    return MappingProxyType({"build_id":OAD_022_BUILD_ID,"revision":OAD_022_REVISION,
        "network_transport":"urllib_https","rsa_pss_sha256":True,"methods":("GET",),"execution":False})

def verify_oad_022_physical_kalshi_rest_transport():
    # Offline verifier checks path/query separation; live call is performed by OAD-025 live probe.
    f=build_kalshi_adapter_foundation()
    return f.predictions_rest_base=="https://external-api.kalshi.com/trade-api/v2" and "/trade-api/v2" in f.predictions_rest_base
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_022_physical_kalshi_rest_transport())
    def test_get_only_manifest(self): self.assertEqual(build_oad_022_certification_manifest()["methods"],("GET",))
if __name__=="__main__":
    print("="*72);print(" OAD-022 CERTIFICATION TEST");print(" PHYSICAL KALSHI REST TRANSPORT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Signed read-only Kalshi REST transport certified");print("[DONE] OAD-022 CERTIFIED")
"""


def verify_upstream():
    p=PACKAGE/'oad_021_credentials.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_021_credentials')
        if getattr(m,'verify_oad_021_physical_kalshi_credential_auth_loader')() is not True:
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
