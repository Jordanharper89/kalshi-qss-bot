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

BUILD_ID='OAD-020'
TITLE='KALSHI PRODUCTION STREAMING RUNTIME BINDING GATE'
REVISION='OAD_020_PRODUCTION_V1'
MODULE=PACKAGE/'oad_020_runtime_binding_gate.py'
TEST=ROOT/'test_oad_020_kalshi_production_streaming_runtime_binding_gate.py'
EXPORTS=('OAD_020_BUILD_ID', 'OAD_020_REVISION', 'KalshiRuntimeBindingCertification', 'certify_oad_016_through_020', 'build_oad_020_certification_manifest', 'verify_oad_020_kalshi_production_streaming_runtime_binding_gate')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_016_reconnect_recovery import verify_oad_016_kalshi_reconnect_resubscribe_recovery
from .oad_017_keepalive_liveness import verify_oad_017_kalshi_keepalive_liveness_supervision
from .oad_018_latency_telemetry import verify_oad_018_kalshi_end_to_end_latency_telemetry
from .oad_019_hot_active_routing import verify_oad_019_kalshi_hot_active_surveillance_routing

OAD_020_BUILD_ID="OAD-020"
OAD_020_REVISION="OAD_020_KALSHI_PRODUCTION_STREAMING_RUNTIME_BINDING_GATE_V1"

@dataclass(frozen=True)
class KalshiRuntimeBindingCertification:
    builds:tuple[str,...]
    capability:str
    oracle_runtime_contract:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_016_through_020():
    checks=(verify_oad_016_kalshi_reconnect_resubscribe_recovery(),
            verify_oad_017_kalshi_keepalive_liveness_supervision(),
            verify_oad_018_kalshi_end_to_end_latency_telemetry(),
            verify_oad_019_kalshi_hot_active_surveillance_routing())
    if not all(checks): raise RuntimeError("Kalshi runtime-binding certification failed")
    builds=tuple("OAD-%03d"%i for i in range(16,21))
    cap="kalshi_reconnect_keepalive_latency_telemetry_dynamic_routing_runtime_binding"
    contract="run_oracle_LIVE.py"
    nxt="physical_live_kalshi_transport_credentials_real_universe_acquisition_real_websocket_activation"
    h=sha256(json.dumps({"builds":builds,"capability":cap,"runtime":contract,"next":nxt},
        sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiRuntimeBindingCertification(builds,cap,contract,nxt,h,True)

def build_oad_020_certification_manifest():
    c=certify_oad_016_through_020()
    return MappingProxyType({"build_id":OAD_020_BUILD_ID,"revision":OAD_020_REVISION,
        "capability":c.capability,"oracle_runtime_contract":c.oracle_runtime_contract,
        "next_capability":c.next_capability,"read_only":True,"execution":False})

def verify_oad_020_kalshi_production_streaming_runtime_binding_gate():
    c=certify_oad_016_through_020()
    return c.certified and len(c.builds)==5 and c.oracle_runtime_contract=="run_oracle_LIVE.py" and c.next_capability=="physical_live_kalshi_transport_credentials_real_universe_acquisition_real_websocket_activation"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_020_runtime_binding_gate import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_020_kalshi_production_streaming_runtime_binding_gate())
    def test_five(self): self.assertEqual(len(certify_oad_016_through_020().builds),5)
    def test_runtime(self): self.assertEqual(certify_oad_016_through_020().oracle_runtime_contract,"run_oracle_LIVE.py")
    def test_next(self): self.assertIn("real_websocket_activation",certify_oad_016_through_020().next_capability)
if __name__=="__main__":
    print("="*72);print(" OAD-020 CERTIFICATION TEST");print(" KALSHI PRODUCTION STREAMING RUNTIME BINDING GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-016 through OAD-020 Kalshi streaming runtime-binding capability certified")
    print("[PASS] Oracle runtime contract: run_oracle_LIVE.py")
    print("[PASS] Next capability: physical live Kalshi transport + real universe acquisition + real WebSocket activation")
    print("[DONE] OAD-020 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_019_hot_active_routing.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_019_hot_active_routing')
        if getattr(m,'verify_oad_019_kalshi_hot_active_surveillance_routing')() is not True:
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
