from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent
def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(),SCRIPT_DIR):
        candidates += [base,base/"kalshi-qss-bot"]
        for p in base.parents:candidates += [p,p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try:c=c.resolve()
        except OSError:continue
        if c in seen:continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")
ROOT=locate_repository();PACKAGE=ROOT/"qseries_v2"/"oracle_continuous_learner";INIT=PACKAGE/"__init__.py"
def write_exact(p,t):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(t.lstrip("\n"),encoding="utf-8",newline="\n");os.replace(tmp,p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def update_init(marker,module,exports):
    cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in cur:return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,cur.rstrip()+("\n\n" if cur.strip() else "")+block)
def run_test(p):
    r=subprocess.run([sys.executable,str(p)],cwd=str(ROOT))
    if r.returncode:raise RuntimeError("Certification test failed: "+p.name)

BUILD_ID='OCL-006';TITLE='PROBABILITY CALIBRATION LEARNING';REVISION='OCL_006_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_006_calibration_learning.py';TEST=ROOT/'test_ocl_006_probability_calibration_learning.py';EXPORTS=('OCL_006_BUILD_ID', 'OCL_006_REVISION', 'CalibrationObservation', 'learn_calibration', 'calibration_mean', 'build_ocl_006_certification_manifest', 'verify_ocl_006_probability_calibration_learning')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .ocl_004_learning_event import LearningEvent,verify_learning_event
OCL_006_BUILD_ID="OCL-006";OCL_006_REVISION="OCL_006_PROBABILITY_CALIBRATION_LEARNING_V1"
@dataclass(frozen=True)
class CalibrationObservation:
 event_id:str; forecast_probability:float; outcome:bool; brier_score:float
def learn_calibration(event,probability,outcome):
 if not verify_learning_event(event):raise ValueError("invalid learning event")
 p=float(probability)
 if p<0 or p>1:raise ValueError("probability outside [0,1]")
 y=1.0 if outcome else 0.0
 return CalibrationObservation(event.event_id,p,bool(outcome),(p-y)**2)
def calibration_mean(rows):
 rows=tuple(rows)
 if not rows:raise ValueError("calibration evidence required")
 return sum(x.brier_score for x in rows)/len(rows)
def build_ocl_006_certification_manifest():return MappingProxyType({"build_id":OCL_006_BUILD_ID,"revision":OCL_006_REVISION,"metric":"brier_score","execution":False,"upstream_mutation":False})
def verify_ocl_006_probability_calibration_learning():
 class E:pass
 # verifier uses a structurally valid real event
 from .ocl_003_outcome_observation import build_outcome_observation
 from .ocl_004_learning_event import assemble_learning_event
 o=build_outcome_observation("m","settlement",1,"t","s","a"*64);e=assemble_learning_event("m","b"*64,"c"*64,o)
 return learn_calibration(e,.8,True).brier_score==(.8-1.0)**2
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event
from qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import *
class T(unittest.TestCase):
 def e(self):
  o=build_outcome_observation("m","x",1,"t","s","a"*64);return assemble_learning_event("m","b"*64,"c"*64,o)
 def test_verifier(self):self.assertTrue(verify_ocl_006_probability_calibration_learning())
 def test_brier(self):self.assertAlmostEqual(learn_calibration(self.e(),.8,True).brier_score,.04)
 def test_bounds(self):
  with self.assertRaises(ValueError):learn_calibration(self.e(),1.1,True)
if __name__=="__main__":
 print("="*72);print(" OCL-006 CERTIFICATION TEST");print(" PROBABILITY CALIBRATION LEARNING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Outcome-grounded probability calibration learning certified");print("[DONE] OCL-006 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ocl_005_evidence_ledger.py'
    if not p.is_file():raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches();m=importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_005_evidence_ledger')
        if getattr(m,'verify_ocl_005_learning_evidence_ledger_foundation')() is not True:raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT));verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT);backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec");compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches();name="qseries_v2.oracle_continuous_learner."+MODULE.stem;sys.modules.pop(name,None);m=importlib.import_module(name)
            if getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])() is not True:raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():p.unlink()
            else:p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored");raise
    man={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    d=hashlib.sha256(json.dumps(man,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)));print("[PASS] Updated: "+str(INIT.relative_to(ROOT)));print("[PASS] Wrote: "+TEST.name);print("[PASS] Deterministic install hash: "+d);print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
