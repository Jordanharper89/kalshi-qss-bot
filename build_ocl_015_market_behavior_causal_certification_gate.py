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

BUILD_ID='OCL-015';TITLE='MARKET BEHAVIOR + CAUSAL LEARNING CERTIFICATION GATE';REVISION='OCL_015_PRODUCTION_V1'
MODULE=PACKAGE/'ocl_015_market_behavior_causal_gate.py';TEST=ROOT/'test_ocl_015_market_behavior_causal_certification_gate.py';EXPORTS=('OCL_015_BUILD_ID', 'OCL_015_REVISION', 'MarketBehaviorCausalCertification', 'certify_ocl_011_through_015', 'build_ocl_015_certification_manifest', 'verify_ocl_015_market_behavior_causal_certification_gate')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_011_market_behavior_observation import verify_ocl_011_market_behavior_observation_model
from .ocl_012_market_behavior_learning import verify_ocl_012_market_behavior_learning_engine
from .ocl_013_cross_market_dependency import verify_ocl_013_cross_market_dependency_learning
from .ocl_014_causal_evidence import verify_ocl_014_causal_evidence_learning
OCL_015_BUILD_ID="OCL-015";OCL_015_REVISION="OCL_015_MARKET_BEHAVIOR_CAUSAL_CERTIFICATION_GATE_V1"
def _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()
@dataclass(frozen=True)
class MarketBehaviorCausalCertification:
 builds:tuple[str,...]; capability:str; next_capability:str; certification_hash:str; certified:bool=True
def certify_ocl_011_through_015():
 checks=(verify_ocl_011_market_behavior_observation_model(),verify_ocl_012_market_behavior_learning_engine(),verify_ocl_013_cross_market_dependency_learning(),verify_ocl_014_causal_evidence_learning())
 if not all(checks):raise RuntimeError("capability certification failed")
 builds=tuple("OCL-%03d"%i for i in range(11,16));raw={"builds":builds,"capability":"market_behavior_and_causal_learning","next_capability":"narrative_entity_and_relationship_learning","certified":True}
 return MarketBehaviorCausalCertification(builds,raw["capability"],raw["next_capability"],_h(raw))
def build_ocl_015_certification_manifest():
 c=certify_ocl_011_through_015();return MappingProxyType({"build_id":OCL_015_BUILD_ID,"revision":OCL_015_REVISION,"capability":c.capability,"next_capability":c.next_capability,"certified":True,"execution":False,"publication":False})
def verify_ocl_015_market_behavior_causal_certification_gate():
 c=certify_ocl_011_through_015();return c.certified and len(c.builds)==5 and c.next_capability=="narrative_entity_and_relationship_learning"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_015_market_behavior_causal_gate import *
class T(unittest.TestCase):
 def test_verifier(self):self.assertTrue(verify_ocl_015_market_behavior_causal_certification_gate())
 def test_five_builds(self):self.assertEqual(len(certify_ocl_011_through_015().builds),5)
 def test_next(self):self.assertEqual(certify_ocl_011_through_015().next_capability,"narrative_entity_and_relationship_learning")
if __name__=="__main__":
 print("="*72);print(" OCL-015 CERTIFICATION TEST");print(" MARKET BEHAVIOR + CAUSAL LEARNING CERTIFICATION GATE");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful():raise SystemExit(1)
 print("[PASS] OCL-011 through OCL-015 market-behavior/causal capability certified")
 print("[PASS] Next capability: narrative, entity, and relationship learning");print("[DONE] OCL-015 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'ocl_014_causal_evidence.py'
    if not p.is_file():raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches();m=importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_014_causal_evidence')
        if getattr(m,'verify_ocl_014_causal_evidence_learning')() is not True:raise RuntimeError("Upstream verification failed")
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
