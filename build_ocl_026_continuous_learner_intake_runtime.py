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

BUILD_ID = 'OCL-026'
TITLE = 'CONTINUOUS LEARNER INTAKE RUNTIME'
REVISION = 'OCL_026_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_026_continuous_intake_runtime.py'
TEST = ROOT / 'test_ocl_026_continuous_learner_intake_runtime.py'
EXPORTS = ('OCL_026_BUILD_ID', 'OCL_026_REVISION', 'LearnerRuntimeInput', 'LearnerRuntimeBatch', 'build_runtime_input', 'assemble_runtime_batch', 'verify_runtime_batch', 'build_ocl_026_certification_manifest', 'verify_ocl_026_continuous_learner_intake_runtime')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Any

OCL_026_BUILD_ID="OCL-026"
OCL_026_REVISION="OCL_026_CONTINUOUS_LEARNER_INTAKE_RUNTIME_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class LearnerRuntimeInput:
    sequence:int
    source_kind:str
    source_ref:str
    source_hash:str
    payload:Mapping[str,Any]
    input_hash:str

@dataclass(frozen=True)
class LearnerRuntimeBatch:
    inputs:tuple[LearnerRuntimeInput,...]
    start_sequence:int
    end_sequence:int
    batch_hash:str

def build_runtime_input(sequence,source_kind,source_ref,source_hash,payload):
    if sequence < 1 or not source_kind or not source_ref or len(source_hash)!=64:
        raise ValueError("invalid runtime input identity")
    canonical={str(k):payload[k] for k in sorted(payload)}
    raw={"sequence":sequence,"source_kind":source_kind,"source_ref":source_ref,"source_hash":source_hash,"payload":canonical}
    return LearnerRuntimeInput(sequence,source_kind,source_ref,source_hash,MappingProxyType(canonical),_h(raw))

def assemble_runtime_batch(inputs):
    rows=tuple(sorted(inputs,key=lambda x:x.sequence))
    if not rows: raise ValueError("runtime inputs required")
    seq=[x.sequence for x in rows]
    if len(seq)!=len(set(seq)) or any(b<=a for a,b in zip(seq,seq[1:])):
        raise ValueError("runtime sequence must be unique and monotonic")
    raw={"input_hashes":[x.input_hash for x in rows],"start_sequence":rows[0].sequence,"end_sequence":rows[-1].sequence}
    return LearnerRuntimeBatch(rows,rows[0].sequence,rows[-1].sequence,_h(raw))

def verify_runtime_batch(b):
    raw={"input_hashes":[x.input_hash for x in b.inputs],"start_sequence":b.start_sequence,"end_sequence":b.end_sequence}
    return bool(b.inputs) and b.batch_hash==_h(raw)

def build_ocl_026_certification_manifest():
    return MappingProxyType({"build_id":OCL_026_BUILD_ID,"revision":OCL_026_REVISION,"runtime":"continuous_read_only_intake","postgresql_write":False,"execution":False,"publication":False})

def verify_ocl_026_continuous_learner_intake_runtime():
    a=build_runtime_input(1,"oml","obs:1","a"*64,{"x":1})
    b=build_runtime_input(2,"outcome","out:1","b"*64,{"y":2})
    return verify_runtime_batch(assemble_runtime_batch((b,a)))
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_ocl_026_continuous_learner_intake_runtime())
    def test_ordering(self):
        a=build_runtime_input(2,"x","a","a"*64,{"x":1})
        b=build_runtime_input(1,"x","b","b"*64,{"x":2})
        self.assertEqual(assemble_runtime_batch((a,b)).start_sequence,1)
    def test_duplicate(self):
        a=build_runtime_input(1,"x","a","a"*64,{"x":1})
        with self.assertRaises(ValueError): assemble_runtime_batch((a,a))

if __name__=="__main__":
    print("="*72);print(" OCL-026 CERTIFICATION TEST");print(" CONTINUOUS LEARNER INTAKE RUNTIME");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic continuous learner intake runtime certified")
    print("[DONE] OCL-026 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_025_learner_state_meta_learning_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_025_learner_state_meta_learning_gate')
        if getattr(m, 'verify_ocl_025_learner_state_meta_learning_certification_gate')() is not True:
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
