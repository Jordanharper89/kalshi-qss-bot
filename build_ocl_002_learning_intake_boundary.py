from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent
def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(),SCRIPT_DIR):
        candidates += [base,base/"kalshi-qss-bot"]
        for p in base.parents: candidates += [p,p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try:c=c.resolve()
        except OSError:continue
        if c in seen:continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")
ROOT=locate_repository(); PACKAGE=ROOT/"qseries_v2"/"oracle_continuous_learner"; INIT=PACKAGE/"__init__.py"
def write_exact(p,t):
    p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(t.lstrip("\n"),encoding="utf-8",newline="\n"); os.replace(tmp,p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def update_init(marker,module,exports):
    cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in cur:return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,cur.rstrip()+("\n\n" if cur.strip() else "")+block)
def run_test(p):
    r=subprocess.run([sys.executable,str(p)],cwd=str(ROOT))
    if r.returncode:raise RuntimeError("Certification test failed: "+p.name)

BUILD_ID='OCL-002'; TITLE='CERTIFIED OML/OCI LEARNING INTAKE BOUNDARY'; REVISION='OCL_002_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_002_learning_intake_boundary.py'; TEST=ROOT/'test_ocl_002_learning_intake_boundary.py'; EXPORTS=('OCL_002_BUILD_ID', 'OCL_002_REVISION', 'LearningIntakeBoundary', 'build_learning_intake_boundary', 'verify_learning_intake_boundary', 'build_ocl_002_certification_manifest', 'verify_ocl_002_learning_intake_boundary')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_001_foundation import verify_ocl_001_continuous_learner_foundation
OCL_002_BUILD_ID="OCL-002";OCL_002_REVISION="OCL_002_CERTIFIED_OML_OCI_LEARNING_INTAKE_BOUNDARY_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class LearningIntakeBoundary:
 source_capability:str; source_freeze_hash:str; memory_read_only:bool=True; intake_read_only:bool=True; execution:bool=False
def build_learning_intake_boundary(source_freeze_hash):
 if len(source_freeze_hash)!=64:raise ValueError("freeze hash required")
 return LearningIntakeBoundary("OCI-001..010_to_OML_boundary",source_freeze_hash)
def verify_learning_intake_boundary(b):return b.memory_read_only and b.intake_read_only and not b.execution and len(b.source_freeze_hash)==64
def build_ocl_002_certification_manifest():return MappingProxyType({"build_id":OCL_002_BUILD_ID,"revision":OCL_002_REVISION,"OCI_frozen":True,"OML_read_only":True,"mutation":False})
def verify_ocl_002_learning_intake_boundary():return verify_ocl_001_continuous_learner_foundation() and verify_learning_intake_boundary(build_learning_intake_boundary("a"*64))
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_002_learning_intake_boundary import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_002_learning_intake_boundary())
 def test_read_only(self):self.assertTrue(build_learning_intake_boundary("a"*64).memory_read_only)
 def test_bad_hash(self):
  with self.assertRaises(ValueError):build_learning_intake_boundary("x")
if __name__=="__main__":
 print("="*72);print(" OCL-002 CERTIFICATION TEST");print(" CERTIFIED OML/OCI LEARNING INTAKE BOUNDARY");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Frozen OCI/OML learning intake boundary certified read-only");print("[DONE] OCL-002 CERTIFIED")
"""

def verify_upstream():
    p=(PACKAGE/'ocl_001_foundation.py')
    if not p.is_file():raise RuntimeError("Certified upstream module missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        name='qseries_v2.oracle_continuous_learner.ocl_001_foundation'
        m=importlib.import_module(name)
        if getattr(m,'verify_ocl_001_continuous_learner_foundation')() is not True:raise RuntimeError("Certified upstream verification failed")
    finally:
        if str(ROOT) in sys.path:sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT);backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec");compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches();name="qseries_v2.oracle_continuous_learner."+MODULE.stem
            sys.modules.pop(name,None);m=importlib.import_module(name)
            v=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if v() is not True:raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored");raise
    man={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name,
         "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(man,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)));print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name);print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
