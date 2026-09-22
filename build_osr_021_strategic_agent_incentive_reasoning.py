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
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir(): return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")
ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_scientific_reasoning"
INIT=PACKAGE/"__init__.py"
def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n"); os.replace(tmp,path)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)
def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OSR-021'; TITLE='STRATEGIC AGENT + INCENTIVE REASONING'; REVISION='OSR_021_PRODUCTION_V1'
MODULE=PACKAGE/'osr_021_strategic_agent_incentives.py'; TEST=ROOT/'test_osr_021_strategic_agent_incentive_reasoning.py'; EXPORTS=('OSR_021_BUILD_ID', 'OSR_021_REVISION', 'StrategicAgent', 'IncentiveAssessment', 'assess_incentive', 'rank_agent_actions', 'build_osr_021_certification_manifest', 'verify_osr_021_strategic_agent_incentive_reasoning')
MODULE_SOURCE=r"""
from dataclasses import dataclass
from types import MappingProxyType
OSR_021_BUILD_ID="OSR-021"; OSR_021_REVISION="OSR_021_STRATEGIC_AGENT_INCENTIVE_REASONING_V1"
@dataclass(frozen=True)
class StrategicAgent:
    agent_id:str; objectives:tuple[str,...]; constraints:tuple[str,...]; available_actions:tuple[str,...]
@dataclass(frozen=True)
class IncentiveAssessment:
    agent_id:str; action_id:str; benefit:float; cost:float; constraint_penalty:float; incentive_score:float
def assess_incentive(agent,action_id,benefit,cost,constraint_penalty=0):
    if action_id not in agent.available_actions: raise ValueError("action unavailable to agent")
    vals=tuple(float(x) for x in (benefit,cost,constraint_penalty))
    if any(x<0 for x in vals): raise ValueError("nonnegative values required")
    return IncentiveAssessment(agent.agent_id,action_id,*vals,vals[0]-vals[1]-vals[2])
def rank_agent_actions(agent,assessments):
    rows=tuple(assessments)
    if not rows or any(x.agent_id!=agent.agent_id for x in rows): raise ValueError("matching assessments required")
    return tuple(sorted(rows,key=lambda x:(-x.incentive_score,x.action_id)))
def build_osr_021_certification_manifest(): return MappingProxyType({"build_id":OSR_021_BUILD_ID,"revision":OSR_021_REVISION,"execution":False})
def verify_osr_021_strategic_agent_incentive_reasoning():
    a=StrategicAgent("a",("profit",),(),("hold","act"))
    return rank_agent_actions(a,(assess_incentive(a,"hold",1,1),assess_incentive(a,"act",3,1)))[0].action_id=="act"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_021_strategic_agent_incentives import *
class T(unittest.TestCase):
 def test_verifier(self): self.assertTrue(verify_osr_021_strategic_agent_incentive_reasoning())
 def test_constraint(self):
  a=StrategicAgent("a",(),(),("x",)); self.assertLess(assess_incentive(a,"x",2,0,2).incentive_score,assess_incentive(a,"x",2,0,0).incentive_score)
 def test_unavailable(self):
  with self.assertRaises(ValueError): assess_incentive(StrategicAgent("a",(),(),("x",)),"y",1,0)
if __name__=="__main__":
 print("="*72);print(" OSR-021 CERTIFICATION TEST");print(" STRATEGIC AGENT + INCENTIVE REASONING");print("="*72)
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
 if not r.wasSuccessful(): raise SystemExit(1)
 print("[PASS] Strategic-agent incentive reasoning certified");print("[DONE] OSR-021 CERTIFIED")
"""
def verify_upstream():
    p=PACKAGE/'osr_020_decision_scenario_counterfactual_gate.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_020_decision_scenario_counterfactual_gate')
        if getattr(m,'verify_osr_020_decision_scenario_counterfactual_certification_gate')() is not True: raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def main():
    print("="*72); print(" "+BUILD_ID+" INSTALLER"); print(" "+TITLE); print("="*72)
    print("[BOOT] Revision: "+REVISION); print("[ROOT] "+str(ROOT))
    verify_upstream(); print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT); backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE); write_exact(TEST,TEST_SOURCE); update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec"); compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches(); name="qseries_v2.oracle_scientific_reasoning."+MODULE.stem; sys.modules.pop(name,None)
            m=importlib.import_module(name); verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True: raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored"); raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name,
    "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT))); print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name); print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
