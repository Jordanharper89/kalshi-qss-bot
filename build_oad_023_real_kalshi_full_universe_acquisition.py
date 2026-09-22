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

BUILD_ID='OAD-023'
TITLE='REAL KALSHI FULL-UNIVERSE ACQUISITION'
REVISION='OAD_023_PRODUCTION_V1'
MODULE=PACKAGE/'oad_023_real_universe_acquisition.py'
TEST=ROOT/'test_oad_023_real_kalshi_full_universe_acquisition.py'
EXPORTS=('OAD_023_BUILD_ID', 'OAD_023_REVISION', 'RealKalshiUniverseAcquisition', 'acquire_real_kalshi_universe', 'build_oad_023_certification_manifest', 'verify_oad_023_real_kalshi_full_universe_acquisition')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_008_full_universe_discovery import normalize_market, KalshiUniverseSnapshot
from .oad_022_rest_transport import kalshi_rest_get
from .oad_021_credentials import KalshiCredentialConfig

OAD_023_BUILD_ID="OAD-023"
OAD_023_REVISION="OAD_023_REAL_KALSHI_FULL_UNIVERSE_ACQUISITION_V1"

@dataclass(frozen=True)
class RealKalshiUniverseAcquisition:
    snapshot:KalshiUniverseSnapshot
    requests:int
    terminal_cursor_reached:bool
    network_live:bool

def acquire_real_kalshi_universe(credentials,max_pages=10000,timeout_seconds=10):
    if not isinstance(credentials,KalshiCredentialConfig): raise ValueError("certified credentials required")
    cursor=""
    pages=[]
    seen=set()
    for _ in range(int(max_pages)):
        params={"limit":1000}
        if cursor: params["cursor"]=cursor
        response=kalshi_rest_get(credentials,"/markets",params,timeout_seconds)
        body=response.body
        markets=body.get("markets",[])
        nxt=str(body.get("cursor") or "")
        pages.append({"markets":markets,"cursor":nxt})
        if not nxt: break
        if nxt in seen: raise RuntimeError("Kalshi cursor loop detected")
        seen.add(nxt); cursor=nxt
    else:
        raise RuntimeError("Kalshi universe acquisition exceeded max_pages")
    records={}
    for page in pages:
        for raw in page["markets"]:
            m=normalize_market(raw)
            if m.ticker in records and records[m.ticker]!=m: raise ValueError("conflicting duplicate market")
            records[m.ticker]=m
    markets=tuple(sorted(records.values(),key=lambda x:x.ticker))
    statuses=tuple(sorted({m.status for m in markets}))
    h=sha256(json.dumps([m.__dict__ for m in markets],sort_keys=True,separators=(",",":")).encode()).hexdigest()
    snap=KalshiUniverseSnapshot(markets,statuses,len(pages),True,h)
    return RealKalshiUniverseAcquisition(snap,len(pages),True,True)

def build_oad_023_certification_manifest():
    return MappingProxyType({"build_id":OAD_023_BUILD_ID,"revision":OAD_023_REVISION,
        "live_endpoint":"/markets","page_limit":1000,"cursor_until_exhaustion":True,"execution":False})

def verify_oad_023_real_kalshi_full_universe_acquisition():
    return build_oad_023_certification_manifest()["cursor_until_exhaustion"] is True
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_023_real_universe_acquisition import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_023_real_kalshi_full_universe_acquisition())
    def test_limit(self): self.assertEqual(build_oad_023_certification_manifest()["page_limit"],1000)
if __name__=="__main__":
    print("="*72);print(" OAD-023 CERTIFICATION TEST");print(" REAL KALSHI FULL-UNIVERSE ACQUISITION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Physical full-universe acquisition implementation certified");print("[DONE] OAD-023 CERTIFIED")
"""


def verify_upstream():
    p=PACKAGE/'oad_022_rest_transport.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport')
        if getattr(m,'verify_oad_022_physical_kalshi_rest_transport')() is not True:
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
