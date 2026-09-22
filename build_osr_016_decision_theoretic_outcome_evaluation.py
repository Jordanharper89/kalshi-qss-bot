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

BUILD_ID='OSR-016'
TITLE='DECISION-THEORETIC OUTCOME EVALUATION'
REVISION='OSR_016_PRODUCTION_V1'
MODULE=PACKAGE/'osr_016_decision_outcome_evaluation.py'
TEST=ROOT/'test_osr_016_decision_theoretic_outcome_evaluation.py'
EXPORTS=('OSR_016_BUILD_ID', 'OSR_016_REVISION', 'OutcomeState', 'DecisionTheoreticEvaluation', 'evaluate_outcomes', 'build_osr_016_certification_manifest', 'verify_osr_016_decision_theoretic_outcome_evaluation')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_016_BUILD_ID="OSR-016"
OSR_016_REVISION="OSR_016_DECISION_THEORETIC_OUTCOME_EVALUATION_V1"

@dataclass(frozen=True)
class OutcomeState:
    outcome_id:str
    probability:float
    utility:float
    downside:float

@dataclass(frozen=True)
class DecisionTheoreticEvaluation:
    expected_utility:float
    expected_downside:float
    risk_adjusted_value:float
    outcome_count:int
    abstain:bool

def evaluate_outcomes(outcomes,risk_aversion=.5,minimum_absolute_value=.05):
    rows=tuple(outcomes)
    if not rows:
        raise ValueError("outcomes required")
    if not 0<=risk_aversion<=1:
        raise ValueError("risk_aversion must be normalized")
    total_p=sum(x.probability for x in rows)
    if abs(total_p-1.0)>1e-9:
        raise ValueError("outcome probabilities must sum to one")
    for x in rows:
        if not 0<=x.probability<=1 or x.downside<0:
            raise ValueError("invalid outcome")
    eu=sum(x.probability*x.utility for x in rows)
    ed=sum(x.probability*x.downside for x in rows)
    rav=eu-risk_aversion*ed
    abstain=abs(rav)<minimum_absolute_value
    return DecisionTheoreticEvaluation(eu,ed,rav,len(rows),abstain)

def build_osr_016_certification_manifest():
    return MappingProxyType({"build_id":OSR_016_BUILD_ID,"revision":OSR_016_REVISION,"role":"outcome_evaluation_only","action_authority":False,"execution":False})

def verify_osr_016_decision_theoretic_outcome_evaluation():
    rows=(OutcomeState("up",.6,1,.1),OutcomeState("down",.4,-.5,.8))
    x=evaluate_outcomes(rows,.5)
    return x.outcome_count==2 and isinstance(x.risk_adjusted_value,float)
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_016_decision_outcome_evaluation import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_016_decision_theoretic_outcome_evaluation())
    def test_probability_sum(self):
        with self.assertRaises(ValueError):
            evaluate_outcomes((OutcomeState("a",.8,1,0),OutcomeState("b",.8,0,0)))
    def test_risk_penalty(self):
        rows=(OutcomeState("a",1,1,1),)
        self.assertLess(evaluate_outcomes(rows,1).risk_adjusted_value,evaluate_outcomes(rows,0).risk_adjusted_value)

if __name__=="__main__":
    print("="*72);print(" OSR-016 CERTIFICATION TEST");print(" DECISION-THEORETIC OUTCOME EVALUATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Risk-adjusted decision-theoretic outcome evaluation certified")
    print("[DONE] OSR-016 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_015_uncertainty_information_adversarial_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_015_uncertainty_information_adversarial_gate')
        if getattr(m,'verify_osr_015_uncertainty_information_adversarial_certification_gate')() is not True:
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
