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

BUILD_ID = 'OCL-027'
TITLE = 'INCREMENTAL LEARNER STATE UPDATE RUNTIME'
REVISION = 'OCL_027_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_027_incremental_state_runtime.py'
TEST = ROOT / 'test_ocl_027_incremental_learner_state_update_runtime.py'
EXPORTS = ('OCL_027_BUILD_ID', 'OCL_027_REVISION', 'IncrementalLearnerState', 'genesis_incremental_state', 'apply_runtime_batch', 'verify_incremental_state', 'build_ocl_027_certification_manifest', 'verify_ocl_027_incremental_learner_state_update_runtime')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ocl_026_continuous_intake_runtime import LearnerRuntimeBatch,verify_runtime_batch

OCL_027_BUILD_ID="OCL-027"
OCL_027_REVISION="OCL_027_INCREMENTAL_LEARNER_STATE_UPDATE_RUNTIME_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class IncrementalLearnerState:
    applied_through_sequence:int
    applied_batches:int
    last_batch_hash:str
    parent_state_hash:str
    state_hash:str

def genesis_incremental_state():
    raw={"applied_through_sequence":0,"applied_batches":0,"last_batch_hash":"0"*64,"parent_state_hash":"0"*64}
    return IncrementalLearnerState(0,0,"0"*64,"0"*64,_h(raw))

def apply_runtime_batch(previous,batch):
    if not verify_runtime_batch(batch): raise ValueError("invalid runtime batch")
    if batch.start_sequence <= previous.applied_through_sequence:
        raise ValueError("replay or overlap rejected")
    raw={"applied_through_sequence":batch.end_sequence,"applied_batches":previous.applied_batches+1,"last_batch_hash":batch.batch_hash,"parent_state_hash":previous.state_hash}
    return IncrementalLearnerState(batch.end_sequence,previous.applied_batches+1,batch.batch_hash,previous.state_hash,_h(raw))

def verify_incremental_state(x):
    raw={"applied_through_sequence":x.applied_through_sequence,"applied_batches":x.applied_batches,"last_batch_hash":x.last_batch_hash,"parent_state_hash":x.parent_state_hash}
    return x.state_hash==_h(raw)

def build_ocl_027_certification_manifest():
    return MappingProxyType({"build_id":OCL_027_BUILD_ID,"revision":OCL_027_REVISION,"update":"incremental_hash_chained","historical_rewrite":False,"execution":False})

def verify_ocl_027_incremental_learner_state_update_runtime():
    from .ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
    g=genesis_incremental_state()
    b=assemble_runtime_batch((build_runtime_input(1,"x","r","a"*64,{"x":1}),))
    s=apply_runtime_batch(g,b)
    return verify_incremental_state(g) and verify_incremental_state(s) and s.parent_state_hash==g.state_hash
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input,assemble_runtime_batch
from qseries_v2.oracle_continuous_learner.ocl_027_incremental_state_runtime import *

class T(unittest.TestCase):
    def batch(self,n):
        return assemble_runtime_batch((build_runtime_input(n,"x","r"+str(n),"a"*64,{"n":n}),))
    def test_verifier(self): self.assertTrue(verify_ocl_027_incremental_learner_state_update_runtime())
    def test_chain(self):
        g=genesis_incremental_state();s=apply_runtime_batch(g,self.batch(1));self.assertEqual(s.parent_state_hash,g.state_hash)
    def test_replay_rejected(self):
        g=genesis_incremental_state();b=self.batch(1);s=apply_runtime_batch(g,b)
        with self.assertRaises(ValueError): apply_runtime_batch(s,b)

if __name__=="__main__":
    print("="*72);print(" OCL-027 CERTIFICATION TEST");print(" INCREMENTAL LEARNER STATE UPDATE RUNTIME");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Incremental hash-chained learner-state updates certified")
    print("[DONE] OCL-027 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_026_continuous_intake_runtime.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime')
        if getattr(m, 'verify_ocl_026_continuous_learner_intake_runtime')() is not True:
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
