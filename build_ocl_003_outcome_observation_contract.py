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

BUILD_ID='OCL-003'; TITLE='OUTCOME OBSERVATION CONTRACT'; REVISION='OCL_003_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_003_outcome_observation.py'; TEST=ROOT/'test_ocl_003_outcome_observation_contract.py'; EXPORTS=('OCL_003_BUILD_ID', 'OCL_003_REVISION', 'OutcomeObservation', 'build_outcome_observation', 'verify_outcome_observation', 'build_ocl_003_certification_manifest', 'verify_ocl_003_outcome_observation_contract')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_002_learning_intake_boundary import verify_ocl_002_learning_intake_boundary
OCL_003_BUILD_ID="OCL-003";OCL_003_REVISION="OCL_003_OUTCOME_OBSERVATION_CONTRACT_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class OutcomeObservation:
 subject_id:str; outcome_type:str; observed_value:object; observed_at:str; source_ref:str; source_hash:str; outcome_hash:str
def build_outcome_observation(subject_id,outcome_type,value,observed_at,source_ref,source_hash):
 if not subject_id or not outcome_type or not observed_at or not source_ref:raise ValueError("outcome identity fields required")
 if len(source_hash)!=64:raise ValueError("source hash required")
 raw={"subject_id":subject_id,"outcome_type":outcome_type,"observed_value":value,"observed_at":observed_at,"source_ref":source_ref,"source_hash":source_hash}
 return OutcomeObservation(subject_id,outcome_type,value,observed_at,source_ref,source_hash,_h(raw))
def verify_outcome_observation(o):return len(o.source_hash)==64 and o.outcome_hash==_h({"subject_id":o.subject_id,"outcome_type":o.outcome_type,"observed_value":o.observed_value,"observed_at":o.observed_at,"source_ref":o.source_ref,"source_hash":o.source_hash})
def build_ocl_003_certification_manifest():return MappingProxyType({"build_id":OCL_003_BUILD_ID,"revision":OCL_003_REVISION,"outcomes_are_observations":True,"retroactive_rewrite":False,"execution":False})
def verify_ocl_003_outcome_observation_contract():
 o=build_outcome_observation("m1","settlement",True,"2026-08-12T00:00:00Z","venue:m1","a"*64)
 return verify_ocl_002_learning_intake_boundary() and verify_outcome_observation(o)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_003_outcome_observation_contract())
 def test_deterministic(self):
  a=build_outcome_observation("m","settlement",1,"t","s","a"*64);b=build_outcome_observation("m","settlement",1,"t","s","a"*64);self.assertEqual(a.outcome_hash,b.outcome_hash)
 def test_required(self):
  with self.assertRaises(ValueError):build_outcome_observation("","x",1,"t","s","a"*64)
if __name__=="__main__":
 print("="*72);print(" OCL-003 CERTIFICATION TEST");print(" OUTCOME OBSERVATION CONTRACT");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Immutable outcome-observation contract certified");print("[DONE] OCL-003 CERTIFIED")
"""

def verify_upstream():
    p=(PACKAGE/'ocl_002_learning_intake_boundary.py')
    if not p.is_file():raise RuntimeError("Certified upstream module missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        name='qseries_v2.oracle_continuous_learner.ocl_002_learning_intake_boundary'
        m=importlib.import_module(name)
        if getattr(m,'verify_ocl_002_learning_intake_boundary')() is not True:raise RuntimeError("Certified upstream verification failed")
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
