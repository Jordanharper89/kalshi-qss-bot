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

BUILD_ID = 'OSR-026'
TITLE = 'REASONING CALIBRATION ENGINE'
REVISION = 'OSR_026_PRODUCTION_V1'
MODULE = PACKAGE / 'osr_026_reasoning_calibration.py'
TEST = ROOT / 'test_osr_026_reasoning_calibration_engine.py'
EXPORTS = ('OSR_026_BUILD_ID', 'OSR_026_REVISION', 'CalibrationObservation', 'CalibrationAssessment', 'assess_reasoning_calibration', 'build_osr_026_certification_manifest', 'verify_osr_026_reasoning_calibration_engine')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType

OSR_026_BUILD_ID = "OSR-026"
OSR_026_REVISION = "OSR_026_REASONING_CALIBRATION_ENGINE_V1"

@dataclass(frozen=True)
class CalibrationObservation:
    prediction_id: str
    confidence: float
    outcome: float
    evidence_quality: float

@dataclass(frozen=True)
class CalibrationAssessment:
    count: int
    brier_score: float
    weighted_error: float
    calibration_quality: float
    status: str

def assess_reasoning_calibration(observations):
    rows = tuple(observations)
    if not rows:
        raise ValueError("calibration observations required")

    for x in rows:
        if any(not 0 <= v <= 1 for v in (x.confidence, x.outcome, x.evidence_quality)):
            raise ValueError("normalized calibration values required")

    brier = sum((x.confidence - x.outcome) ** 2 for x in rows) / len(rows)
    weighted = sum(
        abs(x.confidence - x.outcome) * (1 + x.evidence_quality) / 2
        for x in rows
    ) / len(rows)

    quality = max(0.0, 1.0 - weighted)
    status = "calibrated" if quality >= 0.80 else ("watch" if quality >= 0.60 else "poor")

    return CalibrationAssessment(len(rows), brier, weighted, quality, status)

def build_osr_026_certification_manifest():
    return MappingProxyType({
        "build_id": OSR_026_BUILD_ID,
        "revision": OSR_026_REVISION,
        "method": "brier_plus_evidence_weighted_error",
        "execution": False,
        "publication": False,
    })

def verify_osr_026_reasoning_calibration_engine():
    rows = (
        CalibrationObservation("a", 0.9, 1.0, 1.0),
        CalibrationObservation("b", 0.1, 0.0, 1.0),
    )
    result = assess_reasoning_calibration(rows)
    return result.count == 2 and result.status == "calibrated"
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_026_reasoning_calibration import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_osr_026_reasoning_calibration_engine())

    def test_poor_calibration(self):
        x = assess_reasoning_calibration((CalibrationObservation("a", 1.0, 0.0, 1.0),))
        self.assertEqual(x.status, "poor")

    def test_bounds(self):
        with self.assertRaises(ValueError):
            assess_reasoning_calibration((CalibrationObservation("a", 2.0, 0.0, 1.0),))

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-026 CERTIFICATION TEST")
    print(" REASONING CALIBRATION ENGINE")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Evidence-aware reasoning calibration certified")
    print("[DONE] OSR-026 CERTIFIED")
"""

def verify_upstream():
    p = PACKAGE / 'osr_025_game_complex_signal_gate.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_025_game_complex_signal_gate')
        if getattr(m, 'verify_osr_025_game_complex_signal_certification_gate')() is not True:
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
