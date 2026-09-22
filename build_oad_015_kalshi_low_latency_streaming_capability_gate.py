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

BUILD_ID='OAD-015'
TITLE='KALSHI LOW-LATENCY STREAMING CAPABILITY GATE'
REVISION='OAD_015_PRODUCTION_V1'
MODULE=PACKAGE/'oad_015_streaming_gate.py'
TEST=ROOT/'test_oad_015_kalshi_low_latency_streaming_capability_gate.py'
EXPORTS=('OAD_015_BUILD_ID', 'OAD_015_REVISION', 'KalshiStreamingCapabilityCertification', 'certify_oad_011_through_015', 'build_oad_015_certification_manifest', 'verify_oad_015_kalshi_low_latency_streaming_capability_gate')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_011_websocket_foundation import verify_oad_011_kalshi_websocket_market_data_foundation
from .oad_012_subscription_partitioning import verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage
from .oad_013_market_data_normalization import verify_oad_013_kalshi_orderbook_trade_ticker_normalization
from .oad_014_sequence_integrity import verify_oad_014_kalshi_sequence_integrity_gap_detection_resync

OAD_015_BUILD_ID="OAD-015"
OAD_015_REVISION="OAD_015_KALSHI_LOW_LATENCY_STREAMING_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class KalshiStreamingCapabilityCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_011_through_015():
    checks=(verify_oad_011_kalshi_websocket_market_data_foundation(),
            verify_oad_012_kalshi_subscription_partitioning_full_universe_coverage(),
            verify_oad_013_kalshi_orderbook_trade_ticker_normalization(),
            verify_oad_014_kalshi_sequence_integrity_gap_detection_resync())
    if not all(checks): raise RuntimeError("Kalshi low-latency streaming certification failed")
    builds=tuple("OAD-%03d"%i for i in range(11,16))
    cap="kalshi_authenticated_websocket_subscription_partitioning_market_data_normalization_sequence_integrity"
    nxt="kalshi_reconnect_resubscribe_keepalive_latency_telemetry_hot_active_routing_live_runtime_binding"
    h=sha256(json.dumps({"builds":builds,"capability":cap,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiStreamingCapabilityCertification(builds,cap,nxt,h,True)

def build_oad_015_certification_manifest():
    c=certify_oad_011_through_015()
    return MappingProxyType({"build_id":OAD_015_BUILD_ID,"revision":OAD_015_REVISION,
        "capability":c.capability,"next_capability":c.next_capability,"read_only":True,"execution":False})

def verify_oad_015_kalshi_low_latency_streaming_capability_gate():
    c=certify_oad_011_through_015()
    return c.certified and len(c.builds)==5 and c.next_capability=="kalshi_reconnect_resubscribe_keepalive_latency_telemetry_hot_active_routing_live_runtime_binding"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_015_streaming_gate import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_015_kalshi_low_latency_streaming_capability_gate())
    def test_five(self): self.assertEqual(len(certify_oad_011_through_015().builds),5)
    def test_next(self): self.assertIn("live_runtime_binding",certify_oad_011_through_015().next_capability)
if __name__=="__main__":
    print("="*72);print(" OAD-015 CERTIFICATION TEST");print(" KALSHI LOW-LATENCY STREAMING CAPABILITY GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-011 through OAD-015 Kalshi low-latency streaming capability certified")
    print("[PASS] Next capability: reconnect/resubscribe + keepalive + latency telemetry + HOT/ACTIVE routing + Oracle Live Runtime binding")
    print("[DONE] OAD-015 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'oad_014_sequence_integrity.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_014_sequence_integrity')
        if getattr(m,'verify_oad_014_kalshi_sequence_integrity_gap_detection_resync')() is not True:
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
