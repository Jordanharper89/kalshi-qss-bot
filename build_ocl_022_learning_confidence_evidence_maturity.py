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
PACKAGE = ROOT / "qseries_v2" / "oracle_continuous_learner"
INIT = PACKAGE / "__init__.py"

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

BUILD_ID = 'OCL-022'
TITLE = 'LEARNING CONFIDENCE + EVIDENCE MATURITY'
REVISION = 'OCL_022_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_022_learning_maturity.py'
TEST = ROOT / 'test_ocl_022_learning_confidence_evidence_maturity.py'
EXPORTS = ('OCL_022_BUILD_ID', 'OCL_022_REVISION', 'LearningMaturity', 'evaluate_learning_maturity', 'build_ocl_022_certification_manifest', 'verify_ocl_022_learning_confidence_evidence_maturity')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OCL_022_BUILD_ID="OCL-022"
OCL_022_REVISION="OCL_022_LEARNING_CONFIDENCE_EVIDENCE_MATURITY_CORRECTION_V2"

@dataclass(frozen=True)
class LearningMaturity:
    evidence_count:int
    independent_sources:int
    consistency:float
    contradiction_rate:float
    calibration_quality:float
    maturity_score:float
    maturity_band:str

def evaluate_learning_maturity(evidence_count,independent_sources,consistency,contradiction_rate,calibration_quality):
    if evidence_count<0 or independent_sources<0:
        raise ValueError("counts cannot be negative")
    for x in (consistency,contradiction_rate,calibration_quality):
        if not 0<=float(x)<=1: raise ValueError("normalized maturity inputs required")
    volume=evidence_count/(evidence_count+20) if evidence_count else 0.0
    independence=independent_sources/(independent_sources+5) if independent_sources else 0.0
    score=volume*independence*float(consistency)*(1-float(contradiction_rate))*float(calibration_quality)
    band="mature" if score>=.6 else ("developing" if score>=.25 else "immature")
    return LearningMaturity(evidence_count,independent_sources,float(consistency),float(contradiction_rate),float(calibration_quality),score,band)

def build_ocl_022_certification_manifest():
    return MappingProxyType({"build_id":OCL_022_BUILD_ID,"revision":OCL_022_REVISION,"dimensions":"volume+independence+consistency+contradictions+calibration","execution":False})

def verify_ocl_022_learning_confidence_evidence_maturity():
    low=evaluate_learning_maturity(1,1,.5,.5,.5)
    high=evaluate_learning_maturity(500,50,.99,.01,.99)
    return high.maturity_score>low.maturity_score and high.maturity_band=="mature"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_022_learning_confidence_evidence_maturity())
    def test_contradictions_reduce(self):
        a=evaluate_learning_maturity(100,20,.9,0,.9)
        b=evaluate_learning_maturity(100,20,.9,.8,.9)
        self.assertGreater(a.maturity_score,b.maturity_score)
    def test_bounds(self):
        with self.assertRaises(ValueError): evaluate_learning_maturity(1,1,1.2,0,.5)

if __name__=="__main__":
    print("="*72);print(" OCL-022 CERTIFICATION TEST");print(" LEARNING CONFIDENCE + EVIDENCE MATURITY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Evidence maturity and learning-confidence evaluation certified")
    print("[DONE] OCL-022 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_021_unified_learner_state.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_021_unified_learner_state')
        if getattr(m, 'verify_ocl_021_unified_learner_state_aggregation')() is not True:
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
        write_exact(MODULE, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        update_init("# " + BUILD_ID + " exports", MODULE.stem, EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")
        sys.path.insert(0, str(ROOT))
        try:
            importlib.invalidate_caches()
            name = "qseries_v2.oracle_continuous_learner." + MODULE.stem
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
