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

BUILD_ID = 'OCL-023'
TITLE = 'META-LEARNING PERFORMANCE EVALUATION'
REVISION = 'OCL_023_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_023_meta_learning_performance.py'
TEST = ROOT / 'test_ocl_023_meta_learning_performance_evaluation.py'
EXPORTS = ('OCL_023_BUILD_ID', 'OCL_023_REVISION', 'MetaLearningPerformance', 'evaluate_meta_learning_performance', 'build_ocl_023_certification_manifest', 'verify_ocl_023_meta_learning_performance_evaluation')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OCL_023_BUILD_ID="OCL-023"
OCL_023_REVISION="OCL_023_META_LEARNING_PERFORMANCE_EVALUATION_V1"

@dataclass(frozen=True)
class MetaLearningPerformance:
    mechanism_id:str
    evaluation_count:int
    improvement_count:int
    degradation_count:int
    mean_delta:float
    usefulness_score:float
    status:str

def evaluate_meta_learning_performance(mechanism_id,deltas):
    rows=tuple(float(x) for x in deltas)
    if not mechanism_id or not rows: raise ValueError("mechanism evaluations required")
    improve=sum(1 for x in rows if x>0); degrade=sum(1 for x in rows if x<0)
    mean=sum(rows)/len(rows)
    directional=(improve-degrade)/len(rows)
    magnitude=min(1.0,abs(mean))
    score=directional*magnitude
    status="beneficial" if score>.05 else ("harmful" if score<-.05 else "uncertain")
    return MetaLearningPerformance(mechanism_id,len(rows),improve,degrade,mean,score,status)

def build_ocl_023_certification_manifest():
    return MappingProxyType({"build_id":OCL_023_BUILD_ID,"revision":OCL_023_REVISION,"evaluates":"historical_learning_mechanism_performance","self_modifying_code":False,"execution":False})

def verify_ocl_023_meta_learning_performance_evaluation():
    good=evaluate_meta_learning_performance("m",(0.2,0.1,0.3))
    bad=evaluate_meta_learning_performance("n",(-0.2,-0.1,-0.3))
    return good.status=="beneficial" and bad.status=="harmful"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_023_meta_learning_performance import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_023_meta_learning_performance_evaluation())
    def test_uncertain(self): self.assertEqual(evaluate_meta_learning_performance("m",(0.1,-0.1)).status,"uncertain")
    def test_required(self):
        with self.assertRaises(ValueError): evaluate_meta_learning_performance("",(1,))

if __name__=="__main__":
    print("="*72);print(" OCL-023 CERTIFICATION TEST");print(" META-LEARNING PERFORMANCE EVALUATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Historical learning-mechanism performance evaluation certified")
    print("[DONE] OCL-023 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_022_learning_maturity.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity')
        if getattr(m, 'verify_ocl_022_learning_confidence_evidence_maturity')() is not True:
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
