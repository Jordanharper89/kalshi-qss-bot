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

BUILD_ID='OSR-009'
TITLE='BAYESIAN + CAUSAL + TEMPORAL SYNTHESIS'
REVISION='OSR_009_PRODUCTION_V1'
MODULE=PACKAGE/'osr_009_reasoning_synthesis.py'
TEST=ROOT/'test_osr_009_bayesian_causal_temporal_synthesis.py'
EXPORTS=('OSR_009_BUILD_ID', 'OSR_009_REVISION', 'ScientificSynthesis', 'synthesize_bayesian_causal_temporal', 'build_osr_009_certification_manifest', 'verify_osr_009_bayesian_causal_temporal_synthesis')
MODULE_SOURCE=r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .osr_006_bayesian_update import BayesianEvidenceUpdate
from .osr_007_causal_relationship import CausalRelationshipEvaluation
from .osr_008_temporal_sequence import TemporalSequenceAnalysis

OSR_009_BUILD_ID="OSR-009"
OSR_009_REVISION="OSR_009_BAYESIAN_CAUSAL_TEMPORAL_SYNTHESIS_V1"

@dataclass(frozen=True)
class ScientificSynthesis:
    posterior_probability:float
    causal_status:str
    temporal_precedence:bool
    confidence:float
    conclusion_state:str
    abstain:bool

def synthesize_bayesian_causal_temporal(bayesian,causal,temporal,cause_event_id,effect_event_id,minimum_confidence=.6):
    if not isinstance(bayesian,BayesianEvidenceUpdate) or not isinstance(causal,CausalRelationshipEvaluation) or not isinstance(temporal,TemporalSequenceAnalysis):
        raise ValueError("certified reasoning components required")
    temporal_ok=(cause_event_id,effect_event_id) in temporal.causal_precedence_pairs
    causal_factor=1.0 if causal.status=="supported" else (.5 if causal.status=="uncertain" else 0.0)
    temporal_factor=1.0 if temporal_ok else 0.25
    confidence=bayesian.posterior_probability*causal_factor*temporal_factor
    abstain=confidence<float(minimum_confidence)
    state="supported" if not abstain and causal.status=="supported" and temporal_ok else ("contradicted" if causal.status=="contradicted" else "uncertain")
    return ScientificSynthesis(bayesian.posterior_probability,causal.status,temporal_ok,confidence,state,abstain)

def build_osr_009_certification_manifest():
    return MappingProxyType({"build_id":OSR_009_BUILD_ID,"revision":OSR_009_REVISION,"synthesis":"Bayesian+causal+temporal","abstention":True,"execution":False})

def verify_osr_009_bayesian_causal_temporal_synthesis():
    from .osr_006_bayesian_update import bayesian_update
    from .osr_007_causal_relationship import CausalCriterion,evaluate_causal_relationship
    from .osr_008_temporal_sequence import TemporalEvent,analyze_temporal_sequence
    b=bayesian_update(.5,9)
    c=evaluate_causal_relationship("cause","effect",(CausalCriterion("temporal_precedence",True,1),CausalCriterion("mechanism",True,1)))
    t=analyze_temporal_sequence((TemporalEvent("cause",1,"a"*64),TemporalEvent("effect",2,"b"*64)))
    s=synthesize_bayesian_causal_temporal(b,c,t,"cause","effect")
    return not s.abstain and s.conclusion_state=="supported"
"""
TEST_SOURCE=r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_006_bayesian_update import bayesian_update
from qseries_v2.oracle_scientific_reasoning.osr_007_causal_relationship import CausalCriterion,evaluate_causal_relationship
from qseries_v2.oracle_scientific_reasoning.osr_008_temporal_sequence import TemporalEvent,analyze_temporal_sequence
from qseries_v2.oracle_scientific_reasoning.osr_009_reasoning_synthesis import *

class T(unittest.TestCase):
    def components(self,lr=9):
        b=bayesian_update(.5,lr)
        c=evaluate_causal_relationship("c","e",(CausalCriterion("temporal_precedence",True,1),CausalCriterion("mechanism",True,1)))
        t=analyze_temporal_sequence((TemporalEvent("c",1,"a"*64),TemporalEvent("e",2,"b"*64)))
        return b,c,t
    def test_verifier(self): self.assertTrue(verify_osr_009_bayesian_causal_temporal_synthesis())
    def test_abstain_low_bayes(self):
        b,c,t=self.components(.2);self.assertTrue(synthesize_bayesian_causal_temporal(b,c,t,"c","e").abstain)
    def test_temporal_required_for_strength(self):
        b,c,t=self.components();self.assertTrue(synthesize_bayesian_causal_temporal(b,c,t,"e","c").abstain)

if __name__=="__main__":
    print("="*72);print(" OSR-009 CERTIFICATION TEST");print(" BAYESIAN + CAUSAL + TEMPORAL SYNTHESIS");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Bayesian/causal/temporal synthesis with abstention certified")
    print("[DONE] OSR-009 CERTIFIED")
"""

def verify_upstream():
    p=PACKAGE/'osr_008_temporal_sequence.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_008_temporal_sequence')
        if getattr(m,'verify_osr_008_temporal_precedence_event_sequence_reasoning')() is not True:
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
