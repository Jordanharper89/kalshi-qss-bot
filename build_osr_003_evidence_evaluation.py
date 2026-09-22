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

BUILD_ID = 'OSR-003'
TITLE = 'EVIDENCE EVALUATION'
REVISION = 'OSR_003_PRODUCTION_V1'
MODULE = PACKAGE / 'osr_003_evidence_evaluation.py'
TEST = ROOT / 'test_osr_003_evidence_evaluation.py'
EXPORTS = ('OSR_003_BUILD_ID', 'OSR_003_REVISION', 'EvidenceItem', 'HypothesisEvidenceEvaluation', 'evaluate_hypothesis_evidence', 'build_osr_003_certification_manifest', 'verify_osr_003_evidence_evaluation')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .osr_002_hypothesis_formation import ScientificHypothesis

OSR_003_BUILD_ID="OSR-003"
OSR_003_REVISION="OSR_003_EVIDENCE_EVALUATION_V1"

@dataclass(frozen=True)
class EvidenceItem:
    evidence_id:str
    supports:bool
    weight:float
    independence:float
    reliability:float
    evidence_hash:str

@dataclass(frozen=True)
class HypothesisEvidenceEvaluation:
    hypothesis_id:str
    supporting_weight:float
    contradicting_weight:float
    net_evidence:float
    evidence_count:int
    independent_effective_weight:float
    status:str

def evaluate_hypothesis_evidence(hypothesis,evidence):
    if not isinstance(hypothesis,ScientificHypothesis):
        raise ValueError("scientific hypothesis required")
    rows=tuple(evidence)
    if not rows: raise ValueError("evidence required")
    seen=set()
    sup=con=ind=0.0
    for x in rows:
        if x.evidence_id in seen: raise ValueError("duplicate evidence rejected")
        seen.add(x.evidence_id)
        if len(x.evidence_hash)!=64 or not 0<=x.weight<=1 or not 0<=x.independence<=1 or not 0<=x.reliability<=1:
            raise ValueError("invalid evidence")
        effective=x.weight*x.independence*x.reliability
        ind+=effective
        if x.supports: sup+=effective
        else: con+=effective
    total=sup+con
    net=0.0 if total==0 else (sup-con)/total
    status="supported" if net>=.5 else ("contradicted" if net<=-.5 else "uncertain")
    return HypothesisEvidenceEvaluation(hypothesis.hypothesis_id,sup,con,net,len(rows),ind,status)

def build_osr_003_certification_manifest():
    return MappingProxyType({"build_id":OSR_003_BUILD_ID,"revision":OSR_003_REVISION,"dimensions":"weight+independence+reliability+contradiction","correlation_is_not_causation":True,"execution":False})

def verify_osr_003_evidence_evaluation():
    from .osr_001_foundation import build_scientific_reasoning_input
    from .osr_002_hypothesis_formation import form_hypothesis
    i=build_scientific_reasoning_input("a"*64,"why")
    h=form_hypothesis(i,"h","s","m","f",.5)
    e=(EvidenceItem("e1",True,1,1,.9,"b"*64),EvidenceItem("e2",False,.2,1,.8,"c"*64))
    return evaluate_hypothesis_evidence(h,e).status=="supported"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_001_foundation import build_scientific_reasoning_input
from qseries_v2.oracle_scientific_reasoning.osr_002_hypothesis_formation import form_hypothesis
from qseries_v2.oracle_scientific_reasoning.osr_003_evidence_evaluation import *

class T(unittest.TestCase):
    def h(self):
        return form_hypothesis(build_scientific_reasoning_input("a"*64,"q"),"h","s","m","f",.5)
    def test_verifier(self): self.assertTrue(verify_osr_003_evidence_evaluation())
    def test_counterevidence(self):
        e=(EvidenceItem("e",False,1,1,1,"b"*64),)
        self.assertEqual(evaluate_hypothesis_evidence(self.h(),e).status,"contradicted")
    def test_duplicate(self):
        e=EvidenceItem("e",True,1,1,1,"b"*64)
        with self.assertRaises(ValueError): evaluate_hypothesis_evidence(self.h(),(e,e))

if __name__=="__main__":
    print("="*72);print(" OSR-003 CERTIFICATION TEST");print(" EVIDENCE EVALUATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Reliability/independence/counterevidence evaluation certified")
    print("[DONE] OSR-003 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'osr_002_hypothesis_formation.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_002_hypothesis_formation')
        if getattr(m, 'verify_osr_002_hypothesis_formation')() is not True:
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
