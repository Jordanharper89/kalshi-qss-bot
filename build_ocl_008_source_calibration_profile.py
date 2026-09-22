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

BUILD_ID='OCL-008';TITLE='SOURCE CALIBRATION PROFILE';REVISION='OCL_008_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_008_source_calibration_profile.py';TEST=ROOT/'test_ocl_008_source_calibration_profile.py';EXPORTS=('OCL_008_BUILD_ID', 'OCL_008_REVISION', 'SourceCalibrationProfile', 'build_source_calibration_profile', 'build_ocl_008_certification_manifest', 'verify_ocl_008_source_calibration_profile')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
OCL_008_BUILD_ID="OCL-008";OCL_008_REVISION="OCL_008_SOURCE_CALIBRATION_PROFILE_V1"
@dataclass(frozen=True)
class SourceCalibrationProfile:
 source_id:str; reliability:float; mean_brier:float; evidence_count:int; confidence_weight:float
def build_source_calibration_profile(source_id,reliability,mean_brier,evidence_count):
 if not 0<=reliability<=1 or not 0<=mean_brier<=1 or evidence_count<1:raise ValueError("invalid profile evidence")
 weight=reliability*(1-mean_brier)*(evidence_count/(evidence_count+10))
 return SourceCalibrationProfile(source_id,reliability,mean_brier,evidence_count,weight)
def build_ocl_008_certification_manifest():return MappingProxyType({"build_id":OCL_008_BUILD_ID,"revision":OCL_008_REVISION,"combines":"reliability+calibration+evidence_count","decision_authority":False})
def verify_ocl_008_source_calibration_profile():
 p=build_source_calibration_profile("s",.8,.1,20);return 0<p.confidence_weight<1
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_008_source_calibration_profile import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_008_source_calibration_profile())
 def test_more_evidence_more_weight(self):self.assertGreater(build_source_calibration_profile("s",.8,.1,100).confidence_weight,build_source_calibration_profile("s",.8,.1,1).confidence_weight)
 def test_invalid(self):
  with self.assertRaises(ValueError):build_source_calibration_profile("s",2,.1,1)
if __name__=="__main__":
 print("="*72);print(" OCL-008 CERTIFICATION TEST");print(" SOURCE CALIBRATION PROFILE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Reliability/calibration evidence profile certified");print("[DONE] OCL-008 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ocl_007_source_reliability.py'
    if not p.is_file():raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches();m=importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_007_source_reliability')
        if getattr(m,'verify_ocl_007_source_reliability_learning')() is not True:raise RuntimeError("Upstream verification failed")
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
