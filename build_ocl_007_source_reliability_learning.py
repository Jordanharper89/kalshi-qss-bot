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

BUILD_ID='OCL-007';TITLE='SOURCE RELIABILITY LEARNING';REVISION='OCL_007_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_007_source_reliability.py';TEST=ROOT/'test_ocl_007_source_reliability_learning.py';EXPORTS=('OCL_007_BUILD_ID', 'OCL_007_REVISION', 'SourceReliabilityState', 'update_source_reliability', 'build_ocl_007_certification_manifest', 'verify_ocl_007_source_reliability_learning')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
OCL_007_BUILD_ID="OCL-007";OCL_007_REVISION="OCL_007_SOURCE_RELIABILITY_LEARNING_V1"
@dataclass(frozen=True)
class SourceReliabilityState:
 source_id:str; successes:int; failures:int; posterior_mean:float
def update_source_reliability(previous,source_id,correct):
 if previous is not None and previous.source_id!=source_id:raise ValueError("source mismatch")
 s=(previous.successes if previous else 0)+(1 if correct else 0);f=(previous.failures if previous else 0)+(0 if correct else 1)
 return SourceReliabilityState(source_id,s,f,(s+1)/(s+f+2))
def build_ocl_007_certification_manifest():return MappingProxyType({"build_id":OCL_007_BUILD_ID,"revision":OCL_007_REVISION,"model":"beta_1_1_posterior","requires_outcomes":True,"execution":False})
def verify_ocl_007_source_reliability_learning():
 a=update_source_reliability(None,"s",True);b=update_source_reliability(a,"s",False)
 return a.posterior_mean==2/3 and b.posterior_mean==.5
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_007_source_reliability import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_007_source_reliability_learning())
 def test_update(self):self.assertGreater(update_source_reliability(None,"s",True).posterior_mean,.5)
 def test_mismatch(self):
  a=update_source_reliability(None,"a",True)
  with self.assertRaises(ValueError):update_source_reliability(a,"b",True)
if __name__=="__main__":
 print("="*72);print(" OCL-007 CERTIFICATION TEST");print(" SOURCE RELIABILITY LEARNING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Outcome-grounded Bayesian source reliability learning certified");print("[DONE] OCL-007 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ocl_006_calibration_learning.py'
    if not p.is_file():raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches();m=importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning')
        if getattr(m,'verify_ocl_006_probability_calibration_learning')() is not True:raise RuntimeError("Upstream verification failed")
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
