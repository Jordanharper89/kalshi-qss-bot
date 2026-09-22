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

BUILD_ID='OAD-021'
TITLE='PHYSICAL KALSHI CREDENTIAL + AUTH LOADER'
REVISION='OAD_021_PRODUCTION_V1'
MODULE=PACKAGE/'oad_021_credentials.py'
TEST=ROOT/'test_oad_021_physical_kalshi_credential_auth_loader.py'
EXPORTS=('OAD_021_BUILD_ID', 'OAD_021_REVISION', 'KalshiCredentialConfig', 'load_kalshi_credentials', 'redact_credential_config', 'verify_oad_021_physical_kalshi_credential_auth_loader')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
import os

OAD_021_BUILD_ID="OAD-021"
OAD_021_REVISION="OAD_021_PHYSICAL_KALSHI_CREDENTIAL_AUTH_LOADER_V1"

ENV_KEY_CANDIDATES=("KALSHI_API_KEY_ID","KALSHI_API_KEY","KALSHI_KEY_ID")
ENV_PRIVATE_KEY_PATH_CANDIDATES=("KALSHI_PRIVATE_KEY_PATH","KALSHI_PRIVATE_KEY_FILE")
ENV_PRIVATE_KEY_PEM_CANDIDATES=("KALSHI_PRIVATE_KEY_PEM",)

@dataclass(frozen=True)
class KalshiCredentialConfig:
    api_key_id:str
    private_key_pem:str
    source:str
    secret_persisted_by_adapter:bool=False

def _parse_dotenv(path):
    out={}
    p=Path(path)
    if not p.is_file(): return out
    for line in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        s=line.strip()
        if not s or s.startswith("#") or "=" not in s: continue
        k,v=s.split("=",1)
        out[k.strip()]=v.strip().strip('"').strip("'")
    return out

def load_kalshi_credentials(root=None,environ=None):
    env=dict(os.environ if environ is None else environ)
    root=Path(root or Path.cwd())
    dotenv=_parse_dotenv(root/".env")
    merged=dict(dotenv); merged.update({k:v for k,v in env.items() if v is not None})
    key_id=next((merged.get(k,"").strip() for k in ENV_KEY_CANDIDATES if merged.get(k,"").strip()),"")
    pem=next((merged.get(k,"").strip() for k in ENV_PRIVATE_KEY_PEM_CANDIDATES if merged.get(k,"").strip()),"")
    source="environment"
    if not pem:
        key_path=next((merged.get(k,"").strip() for k in ENV_PRIVATE_KEY_PATH_CANDIDATES if merged.get(k,"").strip()),"")
        if key_path:
            p=Path(key_path)
            if not p.is_absolute(): p=root/p
            if not p.is_file(): raise FileNotFoundError("Configured Kalshi private key file not found")
            pem=p.read_text(encoding="utf-8")
            source="private_key_file"
    if not key_id or "PRIVATE KEY" not in pem:
        raise RuntimeError("Kalshi API credentials not configured. Set KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY_PATH (or KALSHI_PRIVATE_KEY_PEM).")
    return KalshiCredentialConfig(key_id,pem,source,False)

def redact_credential_config(cfg):
    return MappingProxyType({"api_key_id_present":bool(cfg.api_key_id),"private_key_present":bool(cfg.private_key_pem),
        "source":cfg.source,"secret_persisted_by_adapter":False})

def verify_oad_021_physical_kalshi_credential_auth_loader():
    fake={"KALSHI_API_KEY_ID":"abc","KALSHI_PRIVATE_KEY_PEM":"-----BEGIN PRIVATE KEY-----\\nX\\n-----END PRIVATE KEY-----"}
    c=load_kalshi_credentials(root=".",environ=fake)
    r=redact_credential_config(c)
    return c.api_key_id=="abc" and r["private_key_present"] and not r["secret_persisted_by_adapter"]
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_021_physical_kalshi_credential_auth_loader())
    def test_missing(self):
        with self.assertRaises(RuntimeError): load_kalshi_credentials(root=".",environ={})
    def test_redaction(self):
        c=KalshiCredentialConfig("id","-----BEGIN PRIVATE KEY-----x","environment")
        self.assertNotIn("private_key_pem",redact_credential_config(c))
if __name__=="__main__":
    print("="*72);print(" OAD-021 CERTIFICATION TEST");print(" PHYSICAL KALSHI CREDENTIAL + AUTH LOADER");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Local-only Kalshi credential loading/redaction certified");print("[DONE] OAD-021 CERTIFIED")
"""


def verify_upstream():
    p=PACKAGE/'oad_020_runtime_binding_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_020_runtime_binding_gate')
        if getattr(m,'verify_oad_020_kalshi_production_streaming_runtime_binding_gate')() is not True:
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
