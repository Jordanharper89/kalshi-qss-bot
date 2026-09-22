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

BUILD_ID = 'OSR-005'
TITLE = 'SCIENTIFIC REASONING FOUNDATION CAPABILITY GATE'
REVISION = 'OSR_005_PRODUCTION_V1'
MODULE = PACKAGE / 'osr_005_foundation_gate.py'
TEST = ROOT / 'test_osr_005_foundation_hypothesis_evidence_certification_gate.py'
EXPORTS = ('OSR_005_BUILD_ID', 'OSR_005_REVISION', 'ScientificReasoningFoundationCertification', 'certify_osr_001_through_005', 'build_osr_005_certification_manifest', 'verify_osr_005_foundation_hypothesis_evidence_certification_gate')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_001_foundation import verify_osr_001_scientific_reasoning_foundation
from .osr_002_hypothesis_formation import verify_osr_002_hypothesis_formation
from .osr_003_evidence_evaluation import verify_osr_003_evidence_evaluation
from .osr_004_competing_hypotheses import verify_osr_004_competing_hypothesis_analysis

OSR_005_BUILD_ID="OSR-005"
OSR_005_REVISION="OSR_005_FOUNDATION_HYPOTHESIS_EVIDENCE_CERTIFICATION_GATE_V1"

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class ScientificReasoningFoundationCertification:
    builds:tuple[str,...]
    capability:str
    next_capability:str
    certification_hash:str
    certified:bool=True

def certify_osr_001_through_005():
    checks=(verify_osr_001_scientific_reasoning_foundation(),verify_osr_002_hypothesis_formation(),verify_osr_003_evidence_evaluation(),verify_osr_004_competing_hypothesis_analysis())
    if not all(checks): raise RuntimeError("Scientific Reasoning foundation certification failed")
    builds=tuple("OSR-%03d"%i for i in range(1,6))
    raw={"builds":builds,"capability":"scientific_hypothesis_and_evidence_reasoning","next_capability":"bayesian_causal_and_temporal_reasoning","certified":True}
    return ScientificReasoningFoundationCertification(builds,raw["capability"],raw["next_capability"],_h(raw))

def build_osr_005_certification_manifest():
    c=certify_osr_001_through_005()
    return MappingProxyType({"build_id":OSR_005_BUILD_ID,"revision":OSR_005_REVISION,"capability":c.capability,"next_capability":c.next_capability,"certified":True,"execution":False,"publication":False})

def verify_osr_005_foundation_hypothesis_evidence_certification_gate():
    c=certify_osr_001_through_005()
    return c.certified and len(c.builds)==5 and c.next_capability=="bayesian_causal_and_temporal_reasoning"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_005_foundation_gate import *

class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_osr_005_foundation_hypothesis_evidence_certification_gate())
    def test_five(self): self.assertEqual(len(certify_osr_001_through_005().builds),5)
    def test_next(self): self.assertEqual(certify_osr_001_through_005().next_capability,"bayesian_causal_and_temporal_reasoning")

if __name__=="__main__":
    print("="*72);print(" OSR-005 CERTIFICATION TEST");print(" SCIENTIFIC REASONING FOUNDATION CAPABILITY GATE");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OSR-001 through OSR-005 scientific hypothesis/evidence capability certified")
    print("[PASS] Next capability: Bayesian, causal, and temporal reasoning")
    print("[DONE] OSR-005 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'osr_004_competing_hypotheses.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_004_competing_hypotheses')
        if getattr(m, 'verify_osr_004_competing_hypothesis_analysis')() is not True:
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
            write_exact(INIT, "Oracle Scientific Reasoning package.\n")
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
