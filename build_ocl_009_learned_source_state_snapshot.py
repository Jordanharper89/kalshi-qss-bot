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

BUILD_ID='OCL-009';TITLE='LEARNED SOURCE STATE SNAPSHOT';REVISION='OCL_009_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_009_learned_source_state.py';TEST=ROOT/'test_ocl_009_learned_source_state_snapshot.py';EXPORTS=('OCL_009_BUILD_ID', 'OCL_009_REVISION', 'LearnedSourceStateSnapshot', 'build_learned_source_state_snapshot', 'build_ocl_009_certification_manifest', 'verify_ocl_009_learned_source_state_snapshot')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_008_source_calibration_profile import SourceCalibrationProfile
OCL_009_BUILD_ID="OCL-009";OCL_009_REVISION="OCL_009_LEARNED_SOURCE_STATE_SNAPSHOT_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class LearnedSourceStateSnapshot:
 profiles:tuple[SourceCalibrationProfile,...]; snapshot_hash:str
def build_learned_source_state_snapshot(profiles):
 rows=tuple(sorted(profiles,key=lambda x:x.source_id))
 if len({x.source_id for x in rows})!=len(rows):raise ValueError("duplicate source profile")
 raw=[{"source_id":x.source_id,"reliability":x.reliability,"mean_brier":x.mean_brier,"evidence_count":x.evidence_count,"confidence_weight":x.confidence_weight} for x in rows]
 return LearnedSourceStateSnapshot(rows,_h(raw))
def build_ocl_009_certification_manifest():return MappingProxyType({"build_id":OCL_009_BUILD_ID,"revision":OCL_009_REVISION,"snapshot":"deterministic_read_model","execution":False,"publication":False})
def verify_ocl_009_learned_source_state_snapshot():
 from .ocl_008_source_calibration_profile import build_source_calibration_profile
 a=build_source_calibration_profile("a",.8,.1,10);b=build_source_calibration_profile("b",.7,.2,10)
 return build_learned_source_state_snapshot((b,a)).snapshot_hash==build_learned_source_state_snapshot((a,b)).snapshot_hash
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_008_source_calibration_profile import build_source_calibration_profile
from qseries_v2.oracle_continuous_learner.ocl_009_learned_source_state import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_009_learned_source_state_snapshot())
 def test_deterministic(self):
  a=build_source_calibration_profile("a",.8,.1,5);b=build_source_calibration_profile("b",.7,.2,5);self.assertEqual(build_learned_source_state_snapshot((a,b)).snapshot_hash,build_learned_source_state_snapshot((b,a)).snapshot_hash)
 def test_duplicate(self):
  a=build_source_calibration_profile("a",.8,.1,5)
  with self.assertRaises(ValueError):build_learned_source_state_snapshot((a,a))
if __name__=="__main__":
 print("="*72);print(" OCL-009 CERTIFICATION TEST");print(" LEARNED SOURCE STATE SNAPSHOT");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Deterministic learned source-state snapshot certified");print("[DONE] OCL-009 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ocl_008_source_calibration_profile.py'
    if not p.is_file():raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches();m=importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_008_source_calibration_profile')
        if getattr(m,'verify_ocl_008_source_calibration_profile')() is not True:raise RuntimeError("Upstream verification failed")
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
