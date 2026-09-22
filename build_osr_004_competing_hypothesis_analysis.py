from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates = []
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base / "kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p / "kalshi-qss-bot"]
    seen = set()
    for c in candidates:
        try:
            c = c.resolve()
        except OSError:
            continue
        if c in seen:
            continue
        seen.add(c)
        if (c / "qseries_v2").is_dir():
            return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT = locate_repository()
PACKAGE = ROOT / "qseries_v2" / "oracle_scientific_reasoning"
INIT = PACKAGE / "__init__.py"
OCL_PACKAGE = ROOT / "qseries_v2" / "oracle_continuous_learner"

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text.lstrip("\n"), encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_init(marker, module, exports):
    current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block = marker + "\nfrom ." + module + " import (\n"
    block += "".join("    " + x + ",\n" for x in exports)
    block += ")\n"
    write_exact(INIT, current.rstrip() + ("\n\n" if current.strip() else "") + block)

def run_test(path):
    proc = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
    if proc.returncode:
        raise RuntimeError("Certification test failed: " + path.name)

BUILD_ID = 'OSR-004'
TITLE = 'COMPETING HYPOTHESIS ANALYSIS'
REVISION = 'OSR_004_PRODUCTION_V1'
MODULE = PACKAGE / 'osr_004_competing_hypotheses.py'
TEST = ROOT / 'test_osr_004_competing_hypothesis_analysis.py'
EXPORTS = ('OSR_004_BUILD_ID', 'OSR_004_REVISION', 'CompetingHypothesisScore', 'CompetingHypothesisAnalysis', 'analyze_competing_hypotheses', 'build_osr_004_certification_manifest', 'verify_osr_004_competing_hypothesis_analysis')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from math import log
from types import MappingProxyType
from .osr_002_hypothesis_formation import ScientificHypothesis
from .osr_003_evidence_evaluation import HypothesisEvidenceEvaluation

OSR_004_BUILD_ID="OSR-004"
OSR_004_REVISION="OSR_004_COMPETING_HYPOTHESIS_ANALYSIS_V1"

@dataclass(frozen=True)
class CompetingHypothesisScore:
    hypothesis_id:str
    prior_probability:float
    evidence_score:float
    posterior_weight:float

@dataclass(frozen=True)
class CompetingHypothesisAnalysis:
    scores:tuple[CompetingHypothesisScore,...]
    leading_hypothesis_id:str|None
    normalized_leader_probability:float
    abstain:bool

def analyze_competing_hypotheses(hypotheses,evaluations,minimum_leader_probability=.6):
    hs=tuple(hypotheses); ev={x.hypothesis_id:x for x in evaluations}
    if len(hs)<2: raise ValueError("at least two competing hypotheses required")
    if len({h.hypothesis_id for h in hs})!=len(hs): raise ValueError("duplicate hypothesis")
    raw=[]
    for h in hs:
        if not isinstance(h,ScientificHypothesis) or h.hypothesis_id not in ev:
            raise ValueError("complete hypothesis evaluations required")
        e=ev[h.hypothesis_id]
        likelihood=max(.001,min(.999,(e.net_evidence+1)/2))
        weight=h.prior_probability*likelihood
        raw.append((h,e.net_evidence,weight))
    total=sum(x[2] for x in raw)
    scores=tuple(sorted((CompetingHypothesisScore(h.hypothesis_id,h.prior_probability,e,w/total if total else 0.0) for h,e,w in raw),key=lambda x:(-x.posterior_weight,x.hypothesis_id)))
    leader=scores[0]
    abstain=leader.posterior_weight<float(minimum_leader_probability)
    return CompetingHypothesisAnalysis(scores,None if abstain else leader.hypothesis_id,leader.posterior_weight,abstain)

def build_osr_004_certification_manifest():
    return MappingProxyType({"build_id":OSR_004_BUILD_ID,"revision":OSR_004_REVISION,"competing_hypotheses":True,"abstention":True,"execution":False})

def verify_osr_004_competing_hypothesis_analysis():
    from .osr_001_foundation import build_scientific_reasoning_input
    from .osr_002_hypothesis_formation import form_hypothesis
    from .osr_003_evidence_evaluation import HypothesisEvidenceEvaluation
    i=build_scientific_reasoning_input("a"*64,"q")
    h1=form_hypothesis(i,"h1","s1","m1","f1",.5);h2=form_hypothesis(i,"h2","s2","m2","f2",.5)
    e1=HypothesisEvidenceEvaluation("h1",1,0,.8,2,1,"supported")
    e2=HypothesisEvidenceEvaluation("h2",0,1,-.8,2,1,"contradicted")
    a=analyze_competing_hypotheses((h1,h2),(e1,e2))
    return not a.abstain and a.leading_hypothesis_id=="h1"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_001_foundation import build_scientific_reasoning_input
from qseries_v2.oracle_scientific_reasoning.osr_002_hypothesis_formation import form_hypothesis
from qseries_v2.oracle_scientific_reasoning.osr_003_evidence_evaluation import HypothesisEvidenceEvaluation
from qseries_v2.oracle_scientific_reasoning.osr_004_competing_hypotheses import *

class T(unittest.TestCase):
    def pair(self):
        i=build_scientific_reasoning_input("a"*64,"q")
        return (form_hypothesis(i,"a","a","m","f",.5),form_hypothesis(i,"b","b","m","f",.5))
    def test_verifier(self): self.assertTrue(verify_osr_004_competing_hypothesis_analysis())
    def test_abstain_close(self):
        h=self.pair();e=(HypothesisEvidenceEvaluation("a",1,1,0,2,1,"uncertain"),HypothesisEvidenceEvaluation("b",1,1,0,2,1,"uncertain"))
        self.assertTrue(analyze_competing_hypotheses(h,e).abstain)
    def test_two_required(self):
        h=self.pair()[0];e=HypothesisEvidenceEvaluation("a",1,0,1,1,1,"supported")
        with self.assertRaises(ValueError): analyze_competing_hypotheses((h,),(e,))

if __name__=="__main__":
    print("="*72);print(" OSR-004 CERTIFICATION TEST");print(" COMPETING HYPOTHESIS ANALYSIS");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Competing-hypothesis ranking and abstention certified")
    print("[DONE] OSR-004 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'osr_003_evidence_evaluation.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_003_evidence_evaluation')
        if getattr(m, 'verify_osr_003_evidence_evaluation')() is not True:
            raise RuntimeError("Upstream verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("=" * 72)
    print(" " + BUILD_ID + " INSTALLER")
    print(" " + TITLE)
    print("=" * 72)
    print("[BOOT] Revision: " + REVISION)
    print("[ROOT] " + str(ROOT))
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {p: (p.read_bytes() if p.exists() else None) for p in affected}
    try:
        PACKAGE.mkdir(parents=True, exist_ok=True)
        if not INIT.exists():
            write_exact(INIT, "Oracle Scientific Reasoning package.\n")
        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        update_init("# " + BUILD_ID + " exports", MODULE.stem, EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")
        sys.path.insert(0, str(ROOT))
        try:
            importlib.invalidate_caches()
            name = "qseries_v2.oracle_scientific_reasoning." + MODULE.stem
            sys.modules.pop(name, None)
            m = importlib.import_module(name)
            verifier = getattr(m, [x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p, old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] " + BUILD_ID + " installation failed; affected files restored")
        raise

    manifest = {
        "build_id": BUILD_ID,
        "revision": REVISION,
        "module": str(MODULE.relative_to(ROOT)),
        "test": TEST.name,
        "files": {
            str(MODULE.relative_to(ROOT)): sha(MODULE),
            TEST.name: sha(TEST),
            str(INIT.relative_to(ROOT)): sha(INIT),
        },
    }
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    print("[PASS] Wrote: " + str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: " + str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: " + TEST.name)
    print("[PASS] Deterministic install hash: " + digest)
    print("[DONE] " + BUILD_ID + " INSTALLATION AND CERTIFICATION COMPLETE")

if __name__ == "__main__":
    main()
