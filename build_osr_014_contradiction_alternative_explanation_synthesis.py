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
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
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
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    proc=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OSR-014'
TITLE='CONTRADICTION + ALTERNATIVE EXPLANATION SYNTHESIS'
REVISION='OSR_014_PRODUCTION_V1'
MODULE=PACKAGE/'osr_014_alternative_synthesis.py'
TEST=ROOT/'test_osr_014_contradiction_alternative_explanation_synthesis.py'
EXPORTS=('OSR_014_BUILD_ID', 'OSR_014_REVISION', 'AlternativeExplanation', 'ContradictionAlternativeSynthesis', 'synthesize_alternatives', 'build_osr_014_certification_manifest', 'verify_osr_014_contradiction_alternative_explanation_synthesis')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .osr_011_uncertainty_decomposition import UncertaintyComponents
from .osr_013_adversarial_challenge import AdversarialChallengeResult

OSR_014_BUILD_ID="OSR-014"
OSR_014_REVISION="OSR_014_CONTRADICTION_ALTERNATIVE_EXPLANATION_SYNTHESIS_V1"

@dataclass(frozen=True)
class AlternativeExplanation:
    explanation_id:str
    support:float
    contradiction:float
    plausibility:float

@dataclass(frozen=True)
class ContradictionAlternativeSynthesis:
    leading_explanation_id:str|None
    leading_score:float
    uncertainty:float
    adversarial_vulnerability:float
    abstain:bool
    synthesis_state:str

def synthesize_alternatives(uncertainty,adversarial_result,alternatives,minimum_score=.55):
    if not isinstance(uncertainty,UncertaintyComponents) or not isinstance(adversarial_result,AdversarialChallengeResult):
        raise ValueError("certified uncertainty and adversarial results required")
    rows=tuple(alternatives)
    if not rows: raise ValueError("alternative explanations required")
    scored=[]
    for x in rows:
        if not 0<=x.support<=1 or not 0<=x.contradiction<=1 or not 0<=x.plausibility<=1:
            raise ValueError("normalized alternative explanation values required")
        base=x.support*(1-x.contradiction)*x.plausibility
        penalty=(1-uncertainty.total_uncertainty)*(1-adversarial_result.vulnerability_score)
        score=base*(.5+.5*penalty)
        scored.append((score,x.explanation_id))
    scored=sorted(scored,key=lambda x:(-x[0],x[1]))
    leader=scored[0]
    abstain=leader[0]<minimum_score
    state="resolved" if not abstain else ("contested" if uncertainty.total_uncertainty>=.5 or adversarial_result.vulnerability_score>=.5 else "uncertain")
    return ContradictionAlternativeSynthesis(None if abstain else leader[1],leader[0],uncertainty.total_uncertainty,adversarial_result.vulnerability_score,abstain,state)

def build_osr_014_certification_manifest():
    return MappingProxyType({"build_id":OSR_014_BUILD_ID,"revision":OSR_014_REVISION,"combines":"uncertainty+contradiction+adversarial+alternatives","abstention":True,"execution":False})

def verify_osr_014_contradiction_alternative_explanation_synthesis():
    from .osr_011_uncertainty_decomposition import decompose_uncertainty
    from .osr_013_adversarial_challenge import HypothesisChallenge,challenge_hypothesis
    u=decompose_uncertainty(.1,.1,.1,.1,.1)
    a=challenge_hypothesis("h",(HypothesisChallenge("c","a",.1,.1,.1),))
    s=synthesize_alternatives(u,a,(AlternativeExplanation("x",1,0,1),AlternativeExplanation("y",.2,.5,.5)))
    return not s.abstain and s.leading_explanation_id=="x"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_011_uncertainty_decomposition import decompose_uncertainty
from qseries_v2.oracle_scientific_reasoning.osr_013_adversarial_challenge import HypothesisChallenge,challenge_hypothesis
from qseries_v2.oracle_scientific_reasoning.osr_014_alternative_synthesis import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_014_contradiction_alternative_explanation_synthesis())
    def test_abstain_weak(self):
        u=decompose_uncertainty(.8,.8,.8,.8,.8)
        a=challenge_hypothesis("h",(HypothesisChallenge("c","a",1,1,1),))
        s=synthesize_alternatives(u,a,(AlternativeExplanation("x",.3,.5,.5),))
        self.assertTrue(s.abstain)
    def test_invalid_alt(self):
        u=decompose_uncertainty(.1,.1,.1,.1,.1)
        a=challenge_hypothesis("h",(HypothesisChallenge("c","a",.1,.1,.1),))
        with self.assertRaises(ValueError): synthesize_alternatives(u,a,(AlternativeExplanation("x",2,0,1),))

if __name__=="__main__":
    print("="*72);print(" OSR-014 CERTIFICATION TEST");print(" CONTRADICTION + ALTERNATIVE EXPLANATION SYNTHESIS");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Contradiction/alternative synthesis with abstention certified")
    print("[DONE] OSR-014 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_013_adversarial_challenge.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_013_adversarial_challenge')
        if getattr(m,'verify_osr_013_adversarial_hypothesis_challenge_engine')() is not True:
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
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name,
              "files":{str(MODULE.relative_to(ROOT)):sha(MODULE),TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
