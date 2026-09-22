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

BUILD_ID='OAD-010'
TITLE='KALSHI FULL-UNIVERSE DISCOVERY CAPABILITY GATE'
REVISION='OAD_010_PRODUCTION_V1'
MODULE=KALSHI / 'oad_010_kalshi_discovery_gate.py'
TEST=ROOT / 'test_oad_010_kalshi_full_universe_discovery_capability_gate.py'
EXPORTS=('OAD_010_BUILD_ID', 'OAD_010_REVISION', 'KalshiDiscoveryCapabilityCertification', 'certify_oad_006_through_010', 'build_oad_010_certification_manifest', 'verify_oad_010_kalshi_full_universe_discovery_capability_gate')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .oad_006_kalshi_foundation import verify_oad_006_kalshi_adapter_foundation
from .oad_007_transport_auth import verify_oad_007_kalshi_transport_auth_boundary
from .oad_008_full_universe_discovery import verify_oad_008_kalshi_full_universe_discovery
from .oad_009_universe_reconciliation import verify_oad_009_kalshi_universe_reconciliation_lifecycle

OAD_010_BUILD_ID="OAD-010"
OAD_010_REVISION="OAD_010_KALSHI_FULL_UNIVERSE_DISCOVERY_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class KalshiDiscoveryCapabilityCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_oad_006_through_010():
    checks=(verify_oad_006_kalshi_adapter_foundation(),verify_oad_007_kalshi_transport_auth_boundary(),
            verify_oad_008_kalshi_full_universe_discovery(),verify_oad_009_kalshi_universe_reconciliation_lifecycle())
    if not all(checks): raise RuntimeError("Kalshi discovery capability certification failed")
    builds=tuple("OAD-%03d"%i for i in range(6,11))
    capability="kalshi_adapter_foundation_transport_auth_full_universe_discovery_reconciliation_lifecycle"
    nxt="kalshi_low_latency_websocket_market_data_streaming_subscription_partitioning_sequence_integrity"
    h=sha256(json.dumps({"builds":builds,"capability":capability,"next":nxt},sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return KalshiDiscoveryCapabilityCertification(builds,capability,nxt,h,True)

def build_oad_010_certification_manifest():
    c=certify_oad_006_through_010()
    return MappingProxyType({"build_id":OAD_010_BUILD_ID,"revision":OAD_010_REVISION,
        "capability":c.capability,"next_capability":c.next_capability,"read_only":True,"execution":False})

def verify_oad_010_kalshi_full_universe_discovery_capability_gate():
    c=certify_oad_006_through_010()
    return c.certified and len(c.builds)==5 and c.next_capability=="kalshi_low_latency_websocket_market_data_streaming_subscription_partitioning_sequence_integrity"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_010_kalshi_discovery_gate import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_010_kalshi_full_universe_discovery_capability_gate())
    def test_five(self): self.assertEqual(len(certify_oad_006_through_010().builds),5)
    def test_next(self): self.assertIn("low_latency_websocket",certify_oad_006_through_010().next_capability)
if __name__=="__main__":
    print("="*72);print(" OAD-010 CERTIFICATION TEST");print(" KALSHI FULL-UNIVERSE DISCOVERY CAPABILITY GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-006 through OAD-010 Kalshi full-universe discovery capability certified")
    print("[PASS] Next capability: low-latency Kalshi WebSocket market-data streaming + subscription partitioning + sequence integrity")
    print("[DONE] OAD-010 CERTIFIED")
"""

def verify_upstream():
    p=KALSHI / "oad_009_universe_reconciliation.py"
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_009_universe_reconciliation')
        if getattr(m,'verify_oad_009_kalshi_universe_reconciliation_lifecycle')() is not True:
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
