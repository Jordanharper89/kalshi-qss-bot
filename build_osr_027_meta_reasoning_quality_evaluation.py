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

BUILD_ID = 'OSR-027'
TITLE = 'META-REASONING + REASONING-QUALITY EVALUATION'
REVISION = 'OSR_027_PRODUCTION_V1'
MODULE = PACKAGE / 'osr_027_meta_reasoning_quality.py'
TEST = ROOT / 'test_osr_027_meta_reasoning_quality_evaluation.py'
EXPORTS = ('OSR_027_BUILD_ID', 'OSR_027_REVISION', 'ReasoningQualityInput', 'MetaReasoningAssessment', 'evaluate_reasoning_quality', 'build_osr_027_certification_manifest', 'verify_osr_027_meta_reasoning_quality_evaluation')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_027_BUILD_ID = "OSR-027"
OSR_027_REVISION = "OSR_027_META_REASONING_QUALITY_EVALUATION_V1"

@dataclass(frozen=True)
class ReasoningQualityInput:
    capability_id: str
    evidence_coverage: float
    contradiction_control: float
    calibration_quality: float
    replay_integrity: float

@dataclass(frozen=True)
class MetaReasoningAssessment:
    capability_id: str
    quality_score: float
    weakest_dimension: str
    status: str
    abstain: bool

def evaluate_reasoning_quality(x, minimum_quality=0.65):
    vals = {
        "evidence_coverage": float(x.evidence_coverage),
        "contradiction_control": float(x.contradiction_control),
        "calibration_quality": float(x.calibration_quality),
        "replay_integrity": float(x.replay_integrity),
    }
    if any(not 0 <= v <= 1 for v in vals.values()):
        raise ValueError("normalized quality values required")

    score = sum(vals.values()) / len(vals)
    weakest = sorted(vals.items(), key=lambda p: (p[1], p[0]))[0][0]
    abstain = score < minimum_quality

    return MetaReasoningAssessment(
        x.capability_id,
        score,
        weakest,
        "trusted" if not abstain else "insufficient",
        abstain,
    )

def build_osr_027_certification_manifest():
    return MappingProxyType({
        "build_id": OSR_027_BUILD_ID,
        "revision": OSR_027_REVISION,
        "purpose": "reasoning_quality_self_evaluation",
        "abstention": True,
        "execution": False,
    })

def verify_osr_027_meta_reasoning_quality_evaluation():
    x = ReasoningQualityInput("scientific", 1.0, 0.9, 0.9, 1.0)
    return not evaluate_reasoning_quality(x).abstain
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_027_meta_reasoning_quality import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_osr_027_meta_reasoning_quality_evaluation())

    def test_abstain(self):
        x = ReasoningQualityInput("x", 0.1, 0.1, 0.1, 0.1)
        self.assertTrue(evaluate_reasoning_quality(x).abstain)

    def test_weakest(self):
        x = ReasoningQualityInput("x", 1.0, 0.2, 0.8, 0.9)
        self.assertEqual(evaluate_reasoning_quality(x).weakest_dimension, "contradiction_control")

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-027 CERTIFICATION TEST")
    print(" META-REASONING + REASONING-QUALITY EVALUATION")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Meta-reasoning quality evaluation with abstention certified")
    print("[DONE] OSR-027 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'osr_026_reasoning_calibration.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_026_reasoning_calibration')
        if getattr(m, 'verify_osr_026_reasoning_calibration_engine')() is not True:
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
