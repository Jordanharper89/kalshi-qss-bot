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

BUILD_ID = 'OCL-029'
TITLE = 'SCIENTIFIC REASONING HANDOFF CONTRACT'
REVISION = 'OCL_029_PRODUCTION_V1'
MODULE = PACKAGE / 'ocl_029_scientific_reasoning_handoff.py'
TEST = ROOT / 'test_ocl_029_scientific_reasoning_handoff_contract.py'
EXPORTS = ('OCL_029_BUILD_ID', 'OCL_029_REVISION', 'ScientificReasoningHandoff', 'build_scientific_reasoning_handoff', 'verify_scientific_reasoning_handoff', 'build_ocl_029_certification_manifest', 'verify_ocl_029_scientific_reasoning_handoff_contract')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType

OCL_029_BUILD_ID="OCL-029"
OCL_029_REVISION="OCL_029_SCIENTIFIC_REASONING_HANDOFF_CONTRACT_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True)
class ScientificReasoningHandoff:
    learner_state_hash:str
    calibration_state_hash:str
    source_reliability_state_hash:str
    market_behavior_state_hash:str
    causal_state_hash:str
    narrative_state_hash:str
    entity_relationship_state_hash:str
    maturity_state_hash:str
    adaptive_weight_state_hash:str
    handoff_hash:str
    read_only:bool=True
    execution_allowed:bool=False
    publication_allowed:bool=False

def build_scientific_reasoning_handoff(**hashes):
    required=("learner_state_hash","calibration_state_hash","source_reliability_state_hash","market_behavior_state_hash","causal_state_hash","narrative_state_hash","entity_relationship_state_hash","maturity_state_hash","adaptive_weight_state_hash")
    for name in required:
        if name not in hashes or len(hashes[name])!=64:
            raise ValueError("missing certified state hash: "+name)
    raw={k:hashes[k] for k in required}
    raw.update({"read_only":True,"execution_allowed":False,"publication_allowed":False})
    return ScientificReasoningHandoff(**{k:hashes[k] for k in required},handoff_hash=_h(raw))

def verify_scientific_reasoning_handoff(x):
    raw={
        "learner_state_hash":x.learner_state_hash,"calibration_state_hash":x.calibration_state_hash,
        "source_reliability_state_hash":x.source_reliability_state_hash,"market_behavior_state_hash":x.market_behavior_state_hash,
        "causal_state_hash":x.causal_state_hash,"narrative_state_hash":x.narrative_state_hash,
        "entity_relationship_state_hash":x.entity_relationship_state_hash,"maturity_state_hash":x.maturity_state_hash,
        "adaptive_weight_state_hash":x.adaptive_weight_state_hash,"read_only":True,"execution_allowed":False,"publication_allowed":False,
    }
    return x.read_only and not x.execution_allowed and not x.publication_allowed and x.handoff_hash==_h(raw)

def build_ocl_029_certification_manifest():
    return MappingProxyType({"build_id":OCL_029_BUILD_ID,"revision":OCL_029_REVISION,"downstream":"Scientific Reasoning","read_only":True,"execution":False,"publication":False})

def verify_ocl_029_scientific_reasoning_handoff_contract():
    names=("learner_state_hash","calibration_state_hash","source_reliability_state_hash","market_behavior_state_hash","causal_state_hash","narrative_state_hash","entity_relationship_state_hash","maturity_state_hash","adaptive_weight_state_hash")
    h=build_scientific_reasoning_handoff(**{n:("a"*64 if i%2==0 else "b"*64) for i,n in enumerate(names)})
    return verify_scientific_reasoning_handoff(h)
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_continuous_learner.ocl_029_scientific_reasoning_handoff import *

class T(unittest.TestCase):
    def hashes(self):
        names=("learner_state_hash","calibration_state_hash","source_reliability_state_hash","market_behavior_state_hash","causal_state_hash","narrative_state_hash","entity_relationship_state_hash","maturity_state_hash","adaptive_weight_state_hash")
        return {n:"a"*64 for n in names}
    def test_verifier(self): self.assertTrue(verify_ocl_029_scientific_reasoning_handoff_contract())
    def test_read_only(self):
        h=build_scientific_reasoning_handoff(**self.hashes());self.assertTrue(h.read_only);self.assertFalse(h.execution_allowed)
    def test_missing(self):
        d=self.hashes();d.pop("causal_state_hash")
        with self.assertRaises(ValueError):build_scientific_reasoning_handoff(**d)

if __name__=="__main__":
    print("="*72);print(" OCL-029 CERTIFICATION TEST");print(" SCIENTIFIC REASONING HANDOFF CONTRACT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Deterministic read-only Scientific Reasoning handoff certified")
    print("[DONE] OCL-029 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'ocl_028_learning_cycle_orchestrator.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator')
        if getattr(m, 'verify_ocl_028_continuous_learning_cycle_orchestrator')() is not True:
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
