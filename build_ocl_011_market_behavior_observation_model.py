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

BUILD_ID='OCL-011';TITLE='MARKET BEHAVIOR OBSERVATION MODEL';REVISION='OCL_011_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_011_market_behavior_observation.py';TEST=ROOT/'test_ocl_011_market_behavior_observation_model.py';EXPORTS=('OCL_011_BUILD_ID', 'OCL_011_REVISION', 'MarketBehaviorObservation', 'build_market_behavior_observation', 'verify_market_behavior_observation', 'build_ocl_011_certification_manifest', 'verify_ocl_011_market_behavior_observation_model')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
OCL_011_BUILD_ID="OCL-011";OCL_011_REVISION="OCL_011_MARKET_BEHAVIOR_OBSERVATION_MODEL_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
@dataclass(frozen=True)
class MarketBehaviorObservation:
 market_id:str; behavior_type:str; feature_name:str; feature_value:float; observed_at:str; evidence_hash:str; outcome_hash:str; observation_hash:str
def build_market_behavior_observation(market_id,behavior_type,feature_name,feature_value,observed_at,evidence_hash,outcome_hash):
 if not market_id or not behavior_type or not feature_name or not observed_at:raise ValueError("behavior identity fields required")
 for x in (evidence_hash,outcome_hash):
  if len(x)!=64:raise ValueError("sha256 evidence/outcome required")
 raw={"market_id":market_id,"behavior_type":behavior_type,"feature_name":feature_name,"feature_value":float(feature_value),"observed_at":observed_at,"evidence_hash":evidence_hash,"outcome_hash":outcome_hash}
 return MarketBehaviorObservation(market_id,behavior_type,feature_name,float(feature_value),observed_at,evidence_hash,outcome_hash,_h(raw))
def verify_market_behavior_observation(o):
 raw={"market_id":o.market_id,"behavior_type":o.behavior_type,"feature_name":o.feature_name,"feature_value":o.feature_value,"observed_at":o.observed_at,"evidence_hash":o.evidence_hash,"outcome_hash":o.outcome_hash}
 return o.observation_hash==_h(raw)
def build_ocl_011_certification_manifest():return MappingProxyType({"build_id":OCL_011_BUILD_ID,"revision":OCL_011_REVISION,"role":"behavior_observation_not_trade_signal","execution":False})
def verify_ocl_011_market_behavior_observation_model():
 o=build_market_behavior_observation("m","reaction","lag_seconds",4.0,"t","a"*64,"b"*64);return verify_market_behavior_observation(o)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_011_market_behavior_observation import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_011_market_behavior_observation_model())
 def test_deterministic(self):
  a=build_market_behavior_observation("m","r","x",1,"t","a"*64,"b"*64);b=build_market_behavior_observation("m","r","x",1,"t","a"*64,"b"*64);self.assertEqual(a.observation_hash,b.observation_hash)
 def test_bad_hash(self):
  with self.assertRaises(ValueError):build_market_behavior_observation("m","r","x",1,"t","bad","b"*64)
if __name__=="__main__":
 print("="*72);print(" OCL-011 CERTIFICATION TEST");print(" MARKET BEHAVIOR OBSERVATION MODEL");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Outcome-grounded market behavior observation model certified");print("[DONE] OCL-011 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ocl_010_calibration_reliability_gate.py'
    if not p.is_file():raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches();m=importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_010_calibration_reliability_gate')
        if getattr(m,'verify_ocl_010_calibration_source_reliability_certification_gate')() is not True:raise RuntimeError("Upstream verification failed")
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
