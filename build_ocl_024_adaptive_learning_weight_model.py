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

BUILD_ID = 'OCL-024'
TITLE = 'ADAPTIVE LEARNING WEIGHT MODEL'
REVISION = 'OCL_024_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_024_adaptive_learning_weight.py'
TEST = ROOT / 'test_ocl_024_adaptive_learning_weight_model.py'
EXPORTS = ('OCL_024_BUILD_ID', 'OCL_024_REVISION', 'AdaptiveLearningWeight', 'build_adaptive_learning_weight', 'build_ocl_024_certification_manifest', 'verify_ocl_024_adaptive_learning_weight_model')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
from .ocl_023_meta_learning_performance import MetaLearningPerformance

OCL_024_BUILD_ID="OCL-024"
OCL_024_REVISION="OCL_024_ADAPTIVE_LEARNING_WEIGHT_MODEL_V1"

@dataclass(frozen=True)
class AdaptiveLearningWeight:
    mechanism_id:str
    base_weight:float
    performance_score:float
    maturity_score:float
    adjusted_weight:float

def build_adaptive_learning_weight(performance,base_weight,maturity_score):
    if not isinstance(performance,MetaLearningPerformance):
        raise ValueError("certified performance object required")
    if not 0<=base_weight<=1 or not 0<=maturity_score<=1:
        raise ValueError("normalized weights required")
    performance_factor=max(0.0,min(1.0,(performance.usefulness_score+1)/2))
    adjusted=float(base_weight)*(0.25+0.75*performance_factor)*float(maturity_score)
    return AdaptiveLearningWeight(performance.mechanism_id,float(base_weight),performance.usefulness_score,float(maturity_score),adjusted)

def build_ocl_024_certification_manifest():
    return MappingProxyType({"build_id":OCL_024_BUILD_ID,"revision":OCL_024_REVISION,"adaptation":"bounded_weight_only","code_rewrite":False,"execution":False,"publication":False})

def verify_ocl_024_adaptive_learning_weight_model():
    from .ocl_023_meta_learning_performance import evaluate_meta_learning_performance
    good=evaluate_meta_learning_performance("g",(.5,.4,.3))
    bad=evaluate_meta_learning_performance("b",(-.5,-.4,-.3))
    return build_adaptive_learning_weight(good,1,.9).adjusted_weight>build_adaptive_learning_weight(bad,1,.9).adjusted_weight
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import evaluate_meta_learning_performance
from qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_024_adaptive_learning_weight_model())
    def test_bounded(self):
        p=evaluate_meta_learning_performance("m",(1,1,1))
        self.assertLessEqual(build_adaptive_learning_weight(p,1,1).adjusted_weight,1)
    def test_bad_weight(self):
        p=evaluate_meta_learning_performance("m",(1,))
        with self.assertRaises(ValueError): build_adaptive_learning_weight(p,2,1)

if __name__=="__main__":
    print("="*72);print(" OCL-024 CERTIFICATION TEST");print(" ADAPTIVE LEARNING WEIGHT MODEL");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Bounded performance/maturity adaptive learning weights certified")
    print("[DONE] OCL-024 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_023_meta_learning_performance.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance')
        if getattr(m, 'verify_ocl_023_meta_learning_performance_evaluation')() is not True:
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
