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
        try:
            c=c.resolve()
        except OSError:
            continue
        if c in seen:
            continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_intelligence_state"
INIT=PACKAGE/"__init__.py"
OSR_PACKAGE=ROOT/"qseries_v2"/"oracle_scientific_reasoning"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OIS-005'
TITLE='ORACLE INTELLIGENCE STATE FOUNDATION CAPABILITY GATE'
REVISION='OIS_005_PRODUCTION_V1'
MODULE=PACKAGE/'ois_005_foundation_gate.py'
TEST=ROOT/'test_ois_005_intelligence_state_foundation_capability_gate.py'
EXPORTS=('OIS_005_BUILD_ID', 'OIS_005_REVISION', 'IntelligenceStateFoundationCertification', 'certify_ois_001_through_005', 'build_ois_005_certification_manifest', 'verify_ois_005_intelligence_state_foundation_capability_gate')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_001_foundation import verify_ois_001_intelligence_state_foundation
from .ois_002_osr_intake_boundary import verify_ois_002_certified_osr_state_intake_boundary
from .ois_003_canonical_state import verify_ois_003_canonical_intelligence_state_assembly
from .ois_004_query_snapshot import verify_ois_004_read_only_query_snapshot

OIS_005_BUILD_ID="OIS-005"
OIS_005_REVISION="OIS_005_INTELLIGENCE_STATE_FOUNDATION_CAPABILITY_GATE_V1"

@dataclass(frozen=True)
class IntelligenceStateFoundationCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_ois_001_through_005():
    checks=(
        verify_ois_001_intelligence_state_foundation(),
        verify_ois_002_certified_osr_state_intake_boundary(),
        verify_ois_003_canonical_intelligence_state_assembly(),
        verify_ois_004_read_only_query_snapshot(),
    )
    if not all(checks):
        raise RuntimeError("OIS foundation capability certification failed")

    builds=tuple("OIS-%03d"%i for i in range(1,6))
    raw={
        "builds":builds,
        "capability":"canonical_oracle_intelligence_state_foundation",
        "next_capability":"continuous_state_update_persistence_and_runtime",
        "certified":True,
    }
    digest=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return IntelligenceStateFoundationCertification(
        builds,raw["capability"],raw["next_capability"],digest
    )

def build_ois_005_certification_manifest():
    c=certify_ois_001_through_005()
    return MappingProxyType({
        "build_id":OIS_005_BUILD_ID,
        "revision":OIS_005_REVISION,
        "capability":c.capability,
        "next_capability":c.next_capability,
        "certified":True,
        "execution":False,
        "publication":False,
    })

def verify_ois_005_intelligence_state_foundation_capability_gate():
    c=certify_ois_001_through_005()
    return c.certified and len(c.builds)==5 and c.next_capability=="continuous_state_update_persistence_and_runtime"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_intelligence_state.ois_005_foundation_gate import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_005_intelligence_state_foundation_capability_gate())

    def test_five(self):
        self.assertEqual(len(certify_ois_001_through_005().builds),5)

    def test_next(self):
        self.assertEqual(
            certify_ois_001_through_005().next_capability,
            "continuous_state_update_persistence_and_runtime",
        )

if __name__=="__main__":
    print("="*72);print(" OIS-005 CERTIFICATION TEST");print(" ORACLE INTELLIGENCE STATE FOUNDATION CAPABILITY GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OIS-001 through OIS-005 canonical intelligence-state foundation certified")
    print("[PASS] Next capability: continuous state update, persistence, and runtime")
    print("[DONE] OIS-005 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'ois_004_query_snapshot.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_intelligence_state.ois_004_query_snapshot')
        if getattr(m,'verify_ois_004_read_only_query_snapshot')() is not True:
            raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" "+BUILD_ID+" INSTALLER")
    print(" "+TITLE)
    print("="*72)
    print("[BOOT] Revision: "+REVISION)
    print("[ROOT] "+str(ROOT))
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")

    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        PACKAGE.mkdir(parents=True,exist_ok=True)
        if not INIT.exists():
            write_exact(INIT, '"""Oracle Intelligence State - deterministic read-only intelligence-state subsystem."""\n')
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_intelligence_state."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise

    manifest={
        "build_id":BUILD_ID,
        "revision":REVISION,
        "module":str(MODULE.relative_to(ROOT)),
        "test":TEST.name,
        "files":{
            str(MODULE.relative_to(ROOT)):sha(MODULE),
            TEST.name:sha(TEST),
            str(INIT.relative_to(ROOT)):sha(INIT),
        },
    }
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
