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

BUILD_ID='OAD-017'
TITLE='KALSHI KEEPALIVE + CONNECTION LIVENESS SUPERVISION'
REVISION='OAD_017_PRODUCTION_V1'
MODULE=PACKAGE/'oad_017_keepalive_liveness.py'
TEST=ROOT/'test_oad_017_kalshi_keepalive_liveness_supervision.py'
EXPORTS=('OAD_017_BUILD_ID', 'OAD_017_REVISION', 'KeepaliveState', 'evaluate_keepalive', 'should_reconnect_keepalive', 'build_oad_017_certification_manifest', 'verify_oad_017_kalshi_keepalive_liveness_supervision')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType

OAD_017_BUILD_ID="OAD-017"
OAD_017_REVISION="OAD_017_KALSHI_KEEPALIVE_LIVENESS_SUPERVISION_V1"

@dataclass(frozen=True)
class KeepaliveState:
    last_server_ping_ns:int
    last_client_pong_ns:int
    now_ns:int
    ping_interval_seconds:float
    pong_required:bool
    healthy:bool

def evaluate_keepalive(last_server_ping_ns,last_client_pong_ns,now_ns,ping_interval_seconds=10.0,grace_multiplier=2.5):
    vals=(int(last_server_ping_ns),int(last_client_pong_ns),int(now_ns))
    if any(x<0 for x in vals) or float(ping_interval_seconds)<=0 or float(grace_multiplier)<=1:
        raise ValueError("valid keepalive timing required")
    age_s=(vals[2]-vals[0])/1_000_000_000
    pong_ok=vals[1]>=vals[0]
    healthy=age_s<=float(ping_interval_seconds)*float(grace_multiplier) and pong_ok
    return KeepaliveState(vals[0],vals[1],vals[2],float(ping_interval_seconds),True,healthy)

def should_reconnect_keepalive(state):
    if not isinstance(state,KeepaliveState): raise ValueError("certified keepalive state required")
    return not state.healthy

def build_oad_017_certification_manifest():
    return MappingProxyType({"build_id":OAD_017_BUILD_ID,"revision":OAD_017_REVISION,
        "server_ping_interval_seconds":10.0,"pong_required":True,"reconnect_on_liveness_failure":True})

def verify_oad_017_kalshi_keepalive_liveness_supervision():
    good=evaluate_keepalive(0,1,10_000_000_000)
    bad=evaluate_keepalive(0,0,30_000_000_000)
    return good.healthy and should_reconnect_keepalive(bad)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_017_keepalive_liveness import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_017_kalshi_keepalive_liveness_supervision())
    def test_stale_reconnect(self):
        s=evaluate_keepalive(0,0,26_000_000_000)
        self.assertTrue(should_reconnect_keepalive(s))
    def test_recent_healthy(self):
        s=evaluate_keepalive(10_000_000_000,10_000_000_001,15_000_000_000)
        self.assertTrue(s.healthy)
if __name__=="__main__":
    print("="*72);print(" OAD-017 CERTIFICATION TEST");print(" KALSHI KEEPALIVE + CONNECTION LIVENESS SUPERVISION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi Ping/Pong liveness supervision certified");print("[DONE] OAD-017 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_016_reconnect_recovery.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_016_reconnect_recovery')
        if getattr(m,'verify_oad_016_kalshi_reconnect_resubscribe_recovery')() is not True:
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
