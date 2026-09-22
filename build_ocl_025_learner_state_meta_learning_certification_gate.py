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

BUILD_ID = 'OCL-025'
TITLE = 'LEARNER STATE + META-LEARNING CERTIFICATION GATE'
REVISION = 'OCL_025_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_025_learner_state_meta_learning_gate.py'
TEST = ROOT / 'test_ocl_025_learner_state_meta_learning_certification_gate.py'
EXPORTS = ('OCL_025_BUILD_ID', 'OCL_025_REVISION', 'LearnerStateMetaLearningCertification', 'certify_ocl_021_through_025', 'build_ocl_025_certification_manifest', 'verify_ocl_025_learner_state_meta_learning_certification_gate')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_021_unified_learner_state import verify_ocl_021_unified_learner_state_aggregation
from .ocl_022_learning_maturity import verify_ocl_022_learning_confidence_evidence_maturity
from .ocl_023_meta_learning_performance import verify_ocl_023_meta_learning_performance_evaluation
from .ocl_024_adaptive_learning_weight import verify_ocl_024_adaptive_learning_weight_model

OCL_025_BUILD_ID="OCL-025"
OCL_025_REVISION="OCL_025_LEARNER_STATE_META_LEARNING_CERTIFICATION_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class LearnerStateMetaLearningCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_ocl_021_through_025():
    checks=(
        verify_ocl_021_unified_learner_state_aggregation(),
        verify_ocl_022_learning_confidence_evidence_maturity(),
        verify_ocl_023_meta_learning_performance_evaluation(),
        verify_ocl_024_adaptive_learning_weight_model(),
    )
    if not all(checks): raise RuntimeError("capability certification failed")
    builds=tuple("OCL-%03d"%i for i in range(21,26))
    raw={
        "builds":builds,
        "capability":"learner_state_aggregation_and_meta_learning",
        "next_capability":"continuous_learner_runtime_and_scientific_reasoning_handoff",
        "certified":True,
    }
    return LearnerStateMetaLearningCertification(builds,raw["capability"],raw["next_capability"],_h(raw))

def build_ocl_025_certification_manifest():
    c=certify_ocl_021_through_025()
    return MappingProxyType({
        "build_id":OCL_025_BUILD_ID,
        "revision":OCL_025_REVISION,
        "capability":c.capability,
        "next_capability":c.next_capability,
        "certified":True,
        "execution":False,
        "publication":False,
        "self_modifying_code":False,
    })

def verify_ocl_025_learner_state_meta_learning_certification_gate():
    c=certify_ocl_021_through_025()
    return c.certified and len(c.builds)==5 and c.next_capability=="continuous_learner_runtime_and_scientific_reasoning_handoff"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_025_learner_state_meta_learning_gate import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_025_learner_state_meta_learning_certification_gate())
    def test_five_builds(self): self.assertEqual(len(certify_ocl_021_through_025().builds),5)
    def test_next(self): self.assertEqual(certify_ocl_021_through_025().next_capability,"continuous_learner_runtime_and_scientific_reasoning_handoff")

if __name__=="__main__":
    print("="*72);print(" OCL-025 CERTIFICATION TEST");print(" LEARNER STATE + META-LEARNING CERTIFICATION GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OCL-021 through OCL-025 learner-state/meta-learning capability certified")
    print("[PASS] Next capability: Continuous Learner runtime + Scientific Reasoning handoff")
    print("[DONE] OCL-025 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_024_adaptive_learning_weight.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight')
        if getattr(m, 'verify_ocl_024_adaptive_learning_weight_model')() is not True:
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
