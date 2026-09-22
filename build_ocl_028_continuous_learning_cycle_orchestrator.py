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

BUILD_ID = 'OCL-028'
TITLE = 'CONTINUOUS LEARNING CYCLE ORCHESTRATOR'
REVISION = 'OCL_028_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_028_learning_cycle_orchestrator.py'
TEST = ROOT / 'test_ocl_028_continuous_learning_cycle_orchestrator.py'
EXPORTS = ('OCL_028_BUILD_ID', 'OCL_028_REVISION', 'LearningCycleResult', 'run_learning_cycle', 'verify_learning_cycle_result', 'build_ocl_028_certification_manifest', 'verify_ocl_028_continuous_learning_cycle_orchestrator')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_026_continuous_intake_runtime import LearnerRuntimeBatch,verify_runtime_batch
from .ocl_027_incremental_state_runtime import IncrementalLearnerState,apply_runtime_batch,verify_incremental_state

OCL_028_BUILD_ID="OCL-028"
OCL_028_REVISION="OCL_028_CONTINUOUS_LEARNING_CYCLE_ORCHESTRATOR_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class LearningCycleResult:
    cycle_sequence:int
    input_batch_hash:str
    prior_state_hash:str
    new_state_hash:str
    processed_through_sequence:int
    cycle_hash:str
    terminal_dependency:bool=False

def run_learning_cycle(cycle_sequence,state,batch):
    if cycle_sequence<1 or not verify_incremental_state(state) or not verify_runtime_batch(batch):
        raise ValueError("invalid cycle inputs")
    new_state=apply_runtime_batch(state,batch)
    raw={"cycle_sequence":cycle_sequence,"input_batch_hash":batch.batch_hash,"prior_state_hash":state.state_hash,"new_state_hash":new_state.state_hash,"processed_through_sequence":new_state.applied_through_sequence}
    result=LearningCycleResult(cycle_sequence,batch.batch_hash,state.state_hash,new_state.state_hash,new_state.applied_through_sequence,_h(raw),False)
    return result,new_state

def verify_learning_cycle_result(x):
    raw={"cycle_sequence":x.cycle_sequence,"input_batch_hash":x.input_batch_hash,"prior_state_hash":x.prior_state_hash,"new_state_hash":x.new_state_hash,"processed_through_sequence":x.processed_through_sequence}
    return not x.terminal_dependency and x.cycle_hash==_h(raw)

def build_ocl_028_certification_manifest():
    return MappingProxyType({"build_id":OCL_028_BUILD_ID,"revision":OCL_028_REVISION,"mode":"24_7_cycle_ready","terminal_dependency":False,"idempotency":"sequence_and_hash_chain","execution":False})

def verify_ocl_028_continuous_learning_cycle_orchestrator():
    from .ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
    from .ocl_027_incremental_state_runtime import genesis_incremental_state
    b=assemble_runtime_batch((build_runtime_input(1,"x","r","a"*64,{"x":1}),))
    r,s=run_learning_cycle(1,genesis_incremental_state(),b)
    return verify_learning_cycle_result(r) and verify_incremental_state(s)
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import genesis_incremental_state
from qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_028_continuous_learning_cycle_orchestrator())
    def test_terminal_independent(self):
        b=assemble_runtime_batch((build_runtime_input(1,"x","r","a"*64,{"x":1}),))
        r,_=run_learning_cycle(1,genesis_incremental_state(),b);self.assertFalse(r.terminal_dependency)
    def test_cycle_advances(self):
        b=assemble_runtime_batch((build_runtime_input(1,"x","r","a"*64,{"x":1}),))
        _,s=run_learning_cycle(1,genesis_incremental_state(),b);self.assertEqual(s.applied_through_sequence,1)

if __name__=="__main__":
    print("="*72);print(" OCL-028 CERTIFICATION TEST");print(" CONTINUOUS LEARNING CYCLE ORCHESTRATOR");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Terminal-independent 24/7 learning-cycle orchestration certified")
    print("[DONE] OCL-028 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_027_incremental_state_runtime.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime')
        if getattr(m, 'verify_ocl_027_incremental_learner_state_update_runtime')() is not True:
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
