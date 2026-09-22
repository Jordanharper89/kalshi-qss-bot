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

BUILD_ID='OCL-012';TITLE='MARKET BEHAVIOR LEARNING ENGINE';REVISION='OCL_012_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_012_market_behavior_learning.py';TEST=ROOT/'test_ocl_012_market_behavior_learning_engine.py';EXPORTS=('OCL_012_BUILD_ID', 'OCL_012_REVISION', 'MarketBehaviorState', 'learn_market_behavior', 'build_ocl_012_certification_manifest', 'verify_ocl_012_market_behavior_learning_engine')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .ocl_011_market_behavior_observation import MarketBehaviorObservation,verify_market_behavior_observation
OCL_012_BUILD_ID="OCL-012";OCL_012_REVISION="OCL_012_MARKET_BEHAVIOR_LEARNING_ENGINE_V1"
@dataclass(frozen=True)
class MarketBehaviorState:
 market_id:str; behavior_type:str; feature_name:str; evidence_count:int; mean_value:float; mean_absolute_deviation:float; behavior_strength:float
def learn_market_behavior(observations):
 rows=tuple(observations)
 if not rows:raise ValueError("behavior evidence required")
 if not all(verify_market_behavior_observation(x) for x in rows):raise ValueError("invalid behavior observation")
 key={(x.market_id,x.behavior_type,x.feature_name) for x in rows}
 if len(key)!=1:raise ValueError("mixed behavior identities")
 mean=sum(x.feature_value for x in rows)/len(rows);mad=sum(abs(x.feature_value-mean) for x in rows)/len(rows)
 strength=(len(rows)/(len(rows)+5))*(1/(1+mad))
 m,b,f=next(iter(key));return MarketBehaviorState(m,b,f,len(rows),mean,mad,strength)
def build_ocl_012_certification_manifest():return MappingProxyType({"build_id":OCL_012_BUILD_ID,"revision":OCL_012_REVISION,"learning":"repeated_outcome_grounded_behavior","trade_authority":False})
def verify_ocl_012_market_behavior_learning_engine():
 from .ocl_011_market_behavior_observation import build_market_behavior_observation
 rows=tuple(build_market_behavior_observation("m","r","lag",x,"t"+str(x),"a"*64,"b"*64) for x in (2,3,4))
 s=learn_market_behavior(rows);return s.evidence_count==3 and 0<s.behavior_strength<1
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_011_market_behavior_observation import build_market_behavior_observation
from qseries_v2.oracle_continuous_learner.ocl_012_market_behavior_learning import *
class T(unittest.TestCase):
 def o(self,m="m",v=1):return build_market_behavior_observation(m,"r","lag",v,"t"+str(v),"a"*64,"b"*64)
 def test_verifier(self):self.assertTrue(verify_ocl_012_market_behavior_learning_engine())
 def test_count(self):self.assertEqual(learn_market_behavior((self.o(v=1),self.o(v=2))).evidence_count,2)
 def test_mixed(self):
  with self.assertRaises(ValueError):learn_market_behavior((self.o("a"),self.o("b")))
if __name__=="__main__":
 print("="*72);print(" OCL-012 CERTIFICATION TEST");print(" MARKET BEHAVIOR LEARNING ENGINE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] Repeated market behavior learning certified");print("[DONE] OCL-012 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ocl_011_market_behavior_observation.py'
    if not p.is_file():raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches();m=importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_011_market_behavior_observation')
        if getattr(m,'verify_ocl_011_market_behavior_observation_model')() is not True:raise RuntimeError("Upstream verification failed")
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
