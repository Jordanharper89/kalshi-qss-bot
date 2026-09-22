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

BUILD_ID='OCL-001'; TITLE='CONTINUOUS LEARNER FOUNDATION'; REVISION='OCL_001_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_001_foundation.py'; TEST=ROOT/'test_ocl_001_continuous_learner_foundation.py'; EXPORTS=('OCL_001_BUILD_ID', 'OCL_001_REVISION', 'ContinuousLearnerPolicy', 'LearningIdentity', 'build_learning_identity', 'build_ocl_001_certification_manifest', 'verify_ocl_001_continuous_learner_foundation')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from hashlib import sha256
import json
from types import MappingProxyType
OCL_001_BUILD_ID="OCL-001";OCL_001_REVISION="OCL_001_CONTINUOUS_LEARNER_FOUNDATION_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class ContinuousLearnerPolicy:
 deterministic_replay:bool=True; evidence_required:bool=True; outcome_required_for_learning:bool=True
 immutable_source_lineage:bool=True; direct_execution:bool=False; publication:bool=False; upstream_mutation:bool=False
@dataclass(frozen=True)
class LearningIdentity:
 learning_event_id:str; subject_id:str; evidence_hash:str; outcome_hash:str; lineage_hash:str
def build_learning_identity(subject_id,evidence_hash,outcome_hash,lineage_hash):
 for x in (evidence_hash,outcome_hash,lineage_hash):
  if len(x)!=64:raise ValueError("sha256 identity required")
 raw={"subject_id":subject_id,"evidence_hash":evidence_hash,"outcome_hash":outcome_hash,"lineage_hash":lineage_hash}
 return LearningIdentity("learn:"+_h(raw),subject_id,evidence_hash,outcome_hash,lineage_hash)
def build_ocl_001_certification_manifest():
 p=ContinuousLearnerPolicy();return MappingProxyType({"build_id":OCL_001_BUILD_ID,"revision":OCL_001_REVISION,"policy_hash":_h(asdict(p)),"execution":False,"publication":False})
def verify_ocl_001_continuous_learner_foundation():
 p=ContinuousLearnerPolicy();return p.deterministic_replay and p.evidence_required and p.outcome_required_for_learning and not p.direct_execution and not p.upstream_mutation
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_001_foundation import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_001_continuous_learner_foundation())
 def test_identity(self):self.assertEqual(build_learning_identity("x","a"*64,"b"*64,"c"*64).learning_event_id,build_learning_identity("x","a"*64,"b"*64,"c"*64).learning_event_id)
 def test_bad_hash(self):
  with self.assertRaises(ValueError):build_learning_identity("x","bad","b"*64,"c"*64)
 def test_no_execution(self):self.assertFalse(ContinuousLearnerPolicy().direct_execution)
if __name__=="__main__":
 print("="*72);print(" OCL-001 CERTIFICATION TEST");print(" CONTINUOUS LEARNER FOUNDATION");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Deterministic evidence/outcome learning foundation certified");print("[DONE] OCL-001 CERTIFIED")
"""

def verify_upstream():
    p=(ROOT/'qseries_v2'/'oracle_continuous_intake'/'oci_010_capability_certification.py')
    if not p.is_file():raise RuntimeError("Certified upstream module missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        name='qseries_v2.oracle_continuous_intake.oci_010_capability_certification'
        m=importlib.import_module(name)
        if getattr(m,'verify_oci_010_continuous_intake_capability_certification_gate')() is not True:raise RuntimeError("Certified upstream verification failed")
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
