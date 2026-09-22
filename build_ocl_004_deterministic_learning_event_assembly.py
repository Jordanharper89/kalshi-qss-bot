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

BUILD_ID='OCL-004'; TITLE='DETERMINISTIC LEARNING EVENT ASSEMBLY'; REVISION='OCL_004_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_004_learning_event.py'; TEST=ROOT/'test_ocl_004_deterministic_learning_event_assembly.py'; EXPORTS=('OCL_004_BUILD_ID', 'OCL_004_REVISION', 'LearningEvent', 'assemble_learning_event', 'verify_learning_event', 'build_ocl_004_certification_manifest', 'verify_ocl_004_deterministic_learning_event_assembly')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_001_foundation import build_learning_identity
from .ocl_003_outcome_observation import OutcomeObservation,verify_outcome_observation
OCL_004_BUILD_ID="OCL-004";OCL_004_REVISION="OCL_004_DETERMINISTIC_LEARNING_EVENT_ASSEMBLY_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class LearningEvent:
 event_id:str; subject_id:str; evidence_hash:str; outcome_hash:str; lineage_hash:str; outcome_type:str; event_hash:str
def assemble_learning_event(subject_id,evidence_hash,lineage_hash,outcome):
 if not verify_outcome_observation(outcome):raise ValueError("invalid outcome")
 if outcome.subject_id!=subject_id:raise ValueError("subject mismatch")
 ident=build_learning_identity(subject_id,evidence_hash,outcome.outcome_hash,lineage_hash)
 raw={"event_id":ident.learning_event_id,"subject_id":subject_id,"evidence_hash":evidence_hash,"outcome_hash":outcome.outcome_hash,"lineage_hash":lineage_hash,"outcome_type":outcome.outcome_type}
 return LearningEvent(ident.learning_event_id,subject_id,evidence_hash,outcome.outcome_hash,lineage_hash,outcome.outcome_type,_h(raw))
def verify_learning_event(e):return e.event_hash==_h({"event_id":e.event_id,"subject_id":e.subject_id,"evidence_hash":e.evidence_hash,"outcome_hash":e.outcome_hash,"lineage_hash":e.lineage_hash,"outcome_type":e.outcome_type})
def build_ocl_004_certification_manifest():return MappingProxyType({"build_id":OCL_004_BUILD_ID,"revision":OCL_004_REVISION,"deterministic":True,"requires_evidence":True,"requires_outcome":True,"execution":False})
def verify_ocl_004_deterministic_learning_event_assembly():
 from .ocl_003_outcome_observation import build_outcome_observation
 o=build_outcome_observation("m","settlement",1,"t","s","a"*64);e=assemble_learning_event("m","b"*64,"c"*64,o);return verify_learning_event(e)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_004_deterministic_learning_event_assembly())
 def test_subject_mismatch(self):
  o=build_outcome_observation("a","x",1,"t","s","a"*64)
  with self.assertRaises(ValueError):assemble_learning_event("b","b"*64,"c"*64,o)
 def test_replay(self):
  o=build_outcome_observation("m","x",1,"t","s","a"*64);a=assemble_learning_event("m","b"*64,"c"*64,o);b=assemble_learning_event("m","b"*64,"c"*64,o);self.assertEqual(a.event_hash,b.event_hash)
if __name__=="__main__":
 print("="*72);print(" OCL-004 CERTIFICATION TEST");print(" DETERMINISTIC LEARNING EVENT ASSEMBLY");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Evidence + outcome + lineage learning-event assembly certified");print("[DONE] OCL-004 CERTIFIED")
"""

def verify_upstream():
    p=(PACKAGE/'ocl_003_outcome_observation.py')
    if not p.is_file():raise RuntimeError("Certified upstream module missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        name='qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation'
        m=importlib.import_module(name)
        if getattr(m,'verify_ocl_003_outcome_observation_contract')() is not True:raise RuntimeError("Certified upstream verification failed")
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
