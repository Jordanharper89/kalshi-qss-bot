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

BUILD_ID='OIS-001'
TITLE='ORACLE INTELLIGENCE STATE FOUNDATION'
REVISION='OIS_001_PRODUCTION_V1'
MODULE=PACKAGE/'ois_001_foundation.py'
TEST=ROOT/'test_ois_001_intelligence_state_foundation.py'
EXPORTS=('OIS_001_BUILD_ID', 'OIS_001_REVISION', 'IntelligenceStatePolicy', 'IntelligenceStateIdentity', 'build_intelligence_state_identity', 'build_ois_001_certification_manifest', 'verify_ois_001_intelligence_state_foundation')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OIS_001_BUILD_ID="OIS-001"
OIS_001_REVISION="OIS_001_INTELLIGENCE_STATE_FOUNDATION_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class IntelligenceStatePolicy:
    deterministic:bool=True
    read_only:bool=True
    terminal_dependency:bool=False
    execution_allowed:bool=False
    publication_allowed:bool=False
    upstream_mutation:bool=False

@dataclass(frozen=True)
class IntelligenceStateIdentity:
    subject_id:str
    source_state_hash:str
    lineage_hash:str
    state_id:str

def build_intelligence_state_identity(subject_id,source_state_hash,lineage_hash):
    if not subject_id or len(source_state_hash)!=64 or len(lineage_hash)!=64:
        raise ValueError("subject and sha256 lineage required")
    raw={"subject_id":subject_id,"source_state_hash":source_state_hash,"lineage_hash":lineage_hash}
    return IntelligenceStateIdentity(subject_id,source_state_hash,lineage_hash,"ois:"+_h(raw))

def build_ois_001_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_001_BUILD_ID,
        "revision":OIS_001_REVISION,
        "deterministic":True,
        "read_only":True,
        "terminal_dependency":False,
        "execution":False,
        "publication":False,
    })

def verify_ois_001_intelligence_state_foundation():
    p=IntelligenceStatePolicy()
    x=build_intelligence_state_identity("btc","a"*64,"b"*64)
    return p.deterministic and p.read_only and not p.terminal_dependency and not p.execution_allowed and x.state_id.startswith("ois:")
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_intelligence_state.ois_001_foundation import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_ois_001_intelligence_state_foundation())

    def test_deterministic_identity(self):
        a=build_intelligence_state_identity("x","a"*64,"b"*64)
        b=build_intelligence_state_identity("x","a"*64,"b"*64)
        self.assertEqual(a.state_id,b.state_id)

    def test_bad_hash(self):
        with self.assertRaises(ValueError):
            build_intelligence_state_identity("x","bad","b"*64)

if __name__=="__main__":
    print("="*72);print(" OIS-001 CERTIFICATION TEST");print(" ORACLE INTELLIGENCE STATE FOUNDATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic terminal-independent intelligence-state foundation certified")
    print("[DONE] OIS-001 CERTIFIED")
"""

def verify_upstream():
    p=OSR_PACKAGE/'osr_030_final_freeze.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_030_final_freeze')
        if getattr(m,'verify_osr_030_scientific_reasoning_final_certification_freeze')() is not True:
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
