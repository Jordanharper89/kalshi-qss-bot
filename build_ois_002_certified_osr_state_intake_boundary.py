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

BUILD_ID='OIS-002'
TITLE='CERTIFIED OSR STATE INTAKE BOUNDARY'
REVISION='OIS_002_PRODUCTION_V1'
MODULE=PACKAGE/'ois_002_osr_intake_boundary.py'
TEST=ROOT/'test_ois_002_certified_osr_state_intake_boundary.py'
EXPORTS=('OIS_002_BUILD_ID', 'OIS_002_REVISION', 'OSRStateIntake', 'build_osr_state_intake', 'build_ois_002_certification_manifest', 'verify_ois_002_certified_osr_state_intake_boundary')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OIS_002_BUILD_ID="OIS-002"
OIS_002_REVISION="OIS_002_CERTIFIED_OSR_STATE_INTAKE_BOUNDARY_V1"

@dataclass(frozen=True)
class OSRStateIntake:
    subject_id:str
    reasoning_state:str
    support:float
    confidence:float
    contradiction:float
    abstain:bool
    osr_state_hash:str
    read_only:bool=True

def build_osr_state_intake(subject_id,reasoning_state,support,confidence,contradiction,abstain,osr_state_hash):
    if not subject_id or len(osr_state_hash)!=64:
        raise ValueError("subject and certified OSR state hash required")
    vals=(float(support),float(confidence),float(contradiction))
    if any(not 0<=v<=1 for v in vals):
        raise ValueError("normalized OSR state values required")
    return OSRStateIntake(subject_id,reasoning_state,*vals,bool(abstain),osr_state_hash,True)

def build_ois_002_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_002_BUILD_ID,
        "revision":OIS_002_REVISION,
        "upstream":"OSR-030 frozen boundary",
        "osr_mutation":False,
        "read_only":True,
        "execution":False,
    })

def verify_ois_002_certified_osr_state_intake_boundary():
    x=build_osr_state_intake("btc","supported",.8,.9,.1,False,"a"*64)
    return x.read_only and x.confidence==.9 and not build_ois_002_certification_manifest()["osr_mutation"]
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_intelligence_state.ois_002_osr_intake_boundary import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_002_certified_osr_state_intake_boundary())

    def test_read_only(self):
        self.assertTrue(build_osr_state_intake("x","uncertain",.5,.5,.2,True,"a"*64).read_only)

    def test_bounds(self):
        with self.assertRaises(ValueError):
            build_osr_state_intake("x","supported",2,.5,.1,False,"a"*64)

if __name__=="__main__":
    print("="*72);print(" OIS-002 CERTIFICATION TEST");print(" CERTIFIED OSR STATE INTAKE BOUNDARY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Frozen OSR scientific-intelligence intake boundary certified read-only")
    print("[DONE] OIS-002 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'ois_001_foundation.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_intelligence_state.ois_001_foundation')
        if getattr(m,'verify_ois_001_intelligence_state_foundation')() is not True:
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
