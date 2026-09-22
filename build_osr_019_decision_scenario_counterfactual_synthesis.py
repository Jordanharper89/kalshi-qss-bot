from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try:
            c=c.resolve()
        except OSError:
            continue
        if c in seen:
            continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_scientific_reasoning"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OSR-019'
TITLE='DECISION + SCENARIO + COUNTERFACTUAL SYNTHESIS'
REVISION='OSR_019_PRODUCTION_V1'
MODULE=PACKAGE/'osr_019_decision_scenario_counterfactual_synthesis.py'
TEST=ROOT/'test_osr_019_decision_scenario_counterfactual_synthesis.py'
EXPORTS=('OSR_019_BUILD_ID', 'OSR_019_REVISION', 'DecisionScenarioCounterfactualSynthesis', 'synthesize_decision_scenario_counterfactual', 'build_osr_019_certification_manifest', 'verify_osr_019_decision_scenario_counterfactual_synthesis')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .osr_016_decision_outcome_evaluation import DecisionTheoreticEvaluation
from .osr_017_scenario_branching import ScenarioTree
from .osr_018_counterfactual_reasoning import CounterfactualComparison

OSR_019_BUILD_ID="OSR-019"
OSR_019_REVISION="OSR_019_DECISION_SCENARIO_COUNTERFACTUAL_SYNTHESIS_V1"

@dataclass(frozen=True)
class DecisionScenarioCounterfactualSynthesis:
    risk_adjusted_value:float
    scenario_mass:float
    counterfactual_effect:float
    confidence:float
    state:str
    abstain:bool

def synthesize_decision_scenario_counterfactual(decision,scenario,counterfactual,minimum_confidence=.55):
    if not isinstance(decision,DecisionTheoreticEvaluation) or not isinstance(scenario,ScenarioTree) or not isinstance(counterfactual,CounterfactualComparison):
        raise ValueError("certified reasoning components required")
    mass_quality=max(0.0,1-abs(1-scenario.total_leaf_probability))
    identifiability=1.0 if counterfactual.identifiable else .25
    decisiveness=min(1.0,abs(decision.risk_adjusted_value))
    confidence=mass_quality*identifiability*(.5+.5*decisiveness)
    abstain=decision.abstain or confidence<minimum_confidence
    state="supported" if not abstain else "uncertain"
    return DecisionScenarioCounterfactualSynthesis(decision.risk_adjusted_value,scenario.total_leaf_probability,counterfactual.treatment_effect,confidence,state,abstain)

def build_osr_019_certification_manifest():
    return MappingProxyType({"build_id":OSR_019_BUILD_ID,"revision":OSR_019_REVISION,"synthesis":"decision+scenario+counterfactual","abstention":True,"execution":False})

def verify_osr_019_decision_scenario_counterfactual_synthesis():
    from .osr_016_decision_outcome_evaluation import OutcomeState,evaluate_outcomes
    from .osr_017_scenario_branching import make_branch,build_scenario_tree
    from .osr_018_counterfactual_reasoning import evaluate_counterfactual
    d=evaluate_outcomes((OutcomeState("a",1,1,0),),0)
    t=build_scenario_tree((make_branch("r",None,1,"r"),make_branch("a","r",1,"a")))
    c=evaluate_counterfactual(1,0,True)
    s=synthesize_decision_scenario_counterfactual(d,t,c)
    return not s.abstain and s.state=="supported"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_016_decision_outcome_evaluation import OutcomeState,evaluate_outcomes
from qseries_v2.oracle_scientific_reasoning.osr_017_scenario_branching import make_branch,build_scenario_tree
from qseries_v2.oracle_scientific_reasoning.osr_018_counterfactual_reasoning import evaluate_counterfactual
from qseries_v2.oracle_scientific_reasoning.osr_019_decision_scenario_counterfactual_synthesis import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_019_decision_scenario_counterfactual_synthesis())
    def test_unidentifiable_abstains(self):
        d=evaluate_outcomes((OutcomeState("a",1,1,0),),0)
        t=build_scenario_tree((make_branch("r",None,1,"r"),make_branch("a","r",1,"a")))
        c=evaluate_counterfactual(1,0,False)
        self.assertTrue(synthesize_decision_scenario_counterfactual(d,t,c).abstain)

if __name__=="__main__":
    print("="*72);print(" OSR-019 CERTIFICATION TEST");print(" DECISION + SCENARIO + COUNTERFACTUAL SYNTHESIS");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Decision/scenario/counterfactual synthesis with abstention certified")
    print("[DONE] OSR-019 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_018_counterfactual_reasoning.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_018_counterfactual_reasoning')
        if getattr(m,'verify_osr_018_counterfactual_reasoning_engine')() is not True:
            raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" "+BUILD_ID+" INSTALLER")
    print(" "+TITLE)
    print("="*72)
    print("[BOOT] Revision: "+REVISION)
    print("[ROOT] "+str(ROOT))
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_scientific_reasoning."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={
        "build_id":BUILD_ID,
        "revision":REVISION,
        "module":str(MODULE.relative_to(ROOT)),
        "test":TEST.name,
        "files":{
            str(MODULE.relative_to(ROOT)):sha(MODULE),
            TEST.name:sha(TEST),
            str(INIT.relative_to(ROOT)):sha(INIT),
        },
    }
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
