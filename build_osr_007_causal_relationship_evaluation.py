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

BUILD_ID='OSR-007'
TITLE='CAUSAL RELATIONSHIP EVALUATION'
REVISION='OSR_007_PRODUCTION_V1'
MODULE=PACKAGE/'osr_007_causal_relationship.py'
TEST=ROOT/'test_osr_007_causal_relationship_evaluation.py'
EXPORTS=('OSR_007_BUILD_ID', 'OSR_007_REVISION', 'CausalCriterion', 'CausalRelationshipEvaluation', 'evaluate_causal_relationship', 'build_osr_007_certification_manifest', 'verify_osr_007_causal_relationship_evaluation')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_007_BUILD_ID="OSR-007"
OSR_007_REVISION="OSR_007_CAUSAL_RELATIONSHIP_EVALUATION_V1"

@dataclass(frozen=True)
class CausalCriterion:
    name:str
    satisfied:bool
    weight:float

@dataclass(frozen=True)
class CausalRelationshipEvaluation:
    cause_id:str
    effect_id:str
    support_score:float
    counterevidence_score:float
    net_score:float
    satisfied_criteria:int
    status:str

def evaluate_causal_relationship(cause_id,effect_id,criteria,counterevidence_weights=()):
    if not cause_id or not effect_id or cause_id==effect_id:
        raise ValueError("distinct cause/effect identities required")
    rows=tuple(criteria)
    if not rows: raise ValueError("causal criteria required")
    support=0.0; total=0.0; satisfied=0
    for c in rows:
        if not 0<=c.weight<=1: raise ValueError("criterion weight outside [0,1]")
        total+=c.weight
        if c.satisfied:
            support+=c.weight; satisfied+=1
    support_score=0.0 if total==0 else support/total
    counter=sum(max(0.0,min(1.0,float(x))) for x in counterevidence_weights)
    counter_score=min(1.0,counter/len(tuple(counterevidence_weights))) if tuple(counterevidence_weights) else 0.0
    net=support_score-counter_score
    temporal_ok=any(c.name=="temporal_precedence" and c.satisfied for c in rows)
    mechanism_ok=any(c.name=="mechanism" and c.satisfied for c in rows)
    status="supported" if net>=.5 and temporal_ok and mechanism_ok else ("contradicted" if net<=-.5 else "uncertain")
    return CausalRelationshipEvaluation(cause_id,effect_id,support_score,counter_score,net,satisfied,status)

def build_osr_007_certification_manifest():
    return MappingProxyType({"build_id":OSR_007_BUILD_ID,"revision":OSR_007_REVISION,"requires_temporal_precedence":True,"requires_mechanism":True,"supports_counterevidence":True,"execution":False})

def verify_osr_007_causal_relationship_evaluation():
    c=(CausalCriterion("temporal_precedence",True,1),CausalCriterion("mechanism",True,1),CausalCriterion("dose_response",True,.5))
    return evaluate_causal_relationship("a","b",c,()).status=="supported"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_007_causal_relationship import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_007_causal_relationship_evaluation())
    def test_no_temporal_abstains(self):
        c=(CausalCriterion("temporal_precedence",False,1),CausalCriterion("mechanism",True,1))
        self.assertEqual(evaluate_causal_relationship("a","b",c).status,"uncertain")
    def test_counterevidence(self):
        c=(CausalCriterion("temporal_precedence",True,1),CausalCriterion("mechanism",True,1))
        self.assertNotEqual(evaluate_causal_relationship("a","b",c,(1,1)).status,"supported")
    def test_same_identity(self):
        with self.assertRaises(ValueError): evaluate_causal_relationship("a","a",(CausalCriterion("mechanism",True,1),))

if __name__=="__main__":
    print("="*72);print(" OSR-007 CERTIFICATION TEST");print(" CAUSAL RELATIONSHIP EVALUATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Temporal/mechanistic causal evaluation with counterevidence certified")
    print("[DONE] OSR-007 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_006_bayesian_update.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_006_bayesian_update')
        if getattr(m,'verify_osr_006_bayesian_belief_update_engine')() is not True:
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
