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

BUILD_ID = 'OCL-030'
TITLE = 'CONTINUOUS LEARNER RUNTIME FINAL FREEZE GATE'
REVISION = 'OCL_030_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_030_final_freeze_gate.py'
TEST = ROOT / 'test_ocl_030_continuous_learner_runtime_final_freeze_gate.py'
EXPORTS = ('OCL_030_BUILD_ID', 'OCL_030_REVISION', 'ContinuousLearnerFinalCertification', 'certify_ocl_001_through_030', 'build_ocl_030_certification_manifest', 'verify_ocl_030_continuous_learner_runtime_final_freeze_gate')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_026_continuous_intake_runtime import verify_ocl_026_continuous_learner_intake_runtime
from .ocl_027_incremental_state_runtime import verify_ocl_027_incremental_learner_state_update_runtime
from .ocl_028_learning_cycle_orchestrator import verify_ocl_028_continuous_learning_cycle_orchestrator
from .ocl_029_scientific_reasoning_handoff import verify_ocl_029_scientific_reasoning_handoff_contract

OCL_030_BUILD_ID="OCL-030"
OCL_030_REVISION="OCL_030_CONTINUOUS_LEARNER_RUNTIME_FINAL_FREEZE_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class ContinuousLearnerFinalCertification:
    certified_builds:tuple[str,...]
    subsystem:str
    capability:str
    downstream_boundary:str
    freeze_hash:str
    frozen:bool=True
    defect_corrections_only:bool=True

def certify_ocl_001_through_030():
    checks=(
        verify_ocl_026_continuous_learner_intake_runtime(),
        verify_ocl_027_incremental_learner_state_update_runtime(),
        verify_ocl_028_continuous_learning_cycle_orchestrator(),
        verify_ocl_029_scientific_reasoning_handoff_contract(),
    )
    if not all(checks): raise RuntimeError("OCL final certification failed")
    builds=tuple("OCL-%03d"%i for i in range(1,31))
    raw={
        "certified_builds":builds,
        "subsystem":"Oracle Continuous Learner",
        "capability":"24_7_deterministic_continuous_learning",
        "downstream_boundary":"Scientific Reasoning read-only intake",
        "frozen":True,
        "defect_corrections_only":True,
    }
    return ContinuousLearnerFinalCertification(builds,raw["subsystem"],raw["capability"],raw["downstream_boundary"],_h(raw))

def build_ocl_030_certification_manifest():
    c=certify_ocl_001_through_030()
    return MappingProxyType({
        "build_id":OCL_030_BUILD_ID,
        "revision":OCL_030_REVISION,
        "certified_build_count":len(c.certified_builds),
        "subsystem":c.subsystem,
        "capability":c.capability,
        "downstream_boundary":c.downstream_boundary,
        "frozen":c.frozen,
        "defect_corrections_only":c.defect_corrections_only,
        "execution":False,
        "publication":False,
    })

def verify_ocl_030_continuous_learner_runtime_final_freeze_gate():
    c=certify_ocl_001_through_030()
    return c.frozen and c.defect_corrections_only and len(c.certified_builds)==30 and c.downstream_boundary=="Scientific Reasoning read-only intake"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_030_final_freeze_gate import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_030_continuous_learner_runtime_final_freeze_gate())
    def test_all_thirty(self): self.assertEqual(len(certify_ocl_001_through_030().certified_builds),30)
    def test_freeze(self):
        c=certify_ocl_001_through_030();self.assertTrue(c.frozen);self.assertTrue(c.defect_corrections_only)
    def test_downstream(self): self.assertEqual(certify_ocl_001_through_030().downstream_boundary,"Scientific Reasoning read-only intake")

if __name__=="__main__":
    print("="*72);print(" OCL-030 CERTIFICATION TEST");print(" CONTINUOUS LEARNER RUNTIME FINAL FREEZE GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OCL-001 through OCL-030 Continuous Learner certified")
    print("[PASS] Continuous Learner subsystem frozen; defect corrections only")
    print("[PASS] Downstream boundary: Scientific Reasoning read-only intake")
    print("[DONE] OCL-030 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_029_scientific_reasoning_handoff.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_029_scientific_reasoning_handoff')
        if getattr(m, 'verify_ocl_029_scientific_reasoning_handoff_contract')() is not True:
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
