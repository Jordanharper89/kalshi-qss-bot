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

BUILD_ID = 'OSR-001'
TITLE = 'SCIENTIFIC REASONING FOUNDATION'
REVISION = 'OSR_001_CORRECTION_V2_PRODUCTION'
MODULE = PACKAGE / 'osr_001_foundation.py'
TEST = ROOT / 'test_osr_001_scientific_reasoning_foundation.py'
EXPORTS = ('OSR_001_BUILD_ID', 'OSR_001_REVISION', 'ScientificReasoningInput', 'build_scientific_reasoning_input', 'verify_scientific_reasoning_input', 'build_osr_001_certification_manifest', 'verify_osr_001_scientific_reasoning_foundation')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping

OSR_001_BUILD_ID="OSR-001"
OSR_001_REVISION="OSR_001_SCIENTIFIC_REASONING_FOUNDATION_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class ScientificReasoningInput:
    learner_handoff_hash:str
    question:str
    context_hashes:tuple[str,...]
    input_hash:str
    read_only:bool=True

def build_scientific_reasoning_input(learner_handoff_hash,question,context_hashes=()):
    if len(learner_handoff_hash)!=64 or not str(question).strip():
        raise ValueError("certified learner handoff hash and question required")
    hashes=tuple(sorted(context_hashes))
    if any(len(x)!=64 for x in hashes):
        raise ValueError("context hashes must be sha256")
    raw={"learner_handoff_hash":learner_handoff_hash,"question":str(question).strip(),"context_hashes":hashes,"read_only":True}
    return ScientificReasoningInput(learner_handoff_hash,str(question).strip(),hashes,_h(raw),True)

def verify_scientific_reasoning_input(x):
    raw={"learner_handoff_hash":x.learner_handoff_hash,"question":x.question,"context_hashes":x.context_hashes,"read_only":True}
    return x.read_only and x.input_hash==_h(raw)

def build_osr_001_certification_manifest():
    return MappingProxyType({"build_id":OSR_001_BUILD_ID,"revision":OSR_001_REVISION,"upstream":"OCL-030 frozen boundary","reasoning":"read_only","execution":False,"publication":False})

def verify_osr_001_scientific_reasoning_foundation():
    x=build_scientific_reasoning_input("a"*64,"What best explains the observed change?",("b"*64,"c"*64))
    return verify_scientific_reasoning_input(x)
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_001_foundation import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_001_scientific_reasoning_foundation())
    def test_deterministic(self):
        a=build_scientific_reasoning_input("a"*64,"q",("c"*64,"b"*64))
        b=build_scientific_reasoning_input("a"*64,"q",("b"*64,"c"*64))
        self.assertEqual(a.input_hash,b.input_hash)
    def test_bad_hash(self):
        with self.assertRaises(ValueError): build_scientific_reasoning_input("bad","q")

if __name__=="__main__":
    print("="*72);print(" OSR-001 CERTIFICATION TEST");print(" SCIENTIFIC REASONING FOUNDATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic read-only Scientific Reasoning foundation certified")
    print("[DONE] OSR-001 CERTIFIED")
"""

def verify_upstream():
    p = OCL_PACKAGE / 'ocl_030_final_freeze_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_030_final_freeze_gate')
        if getattr(m, 'verify_ocl_030_continuous_learner_runtime_final_freeze_gate')() is not True:
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
            write_exact(INIT, '"""Oracle Scientific Reasoning — deterministic read-only reasoning subsystem."""\n')
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
