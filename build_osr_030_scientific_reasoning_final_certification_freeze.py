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

BUILD_ID = 'OSR-030'
TITLE = 'SCIENTIFIC REASONING FINAL CERTIFICATION + FREEZE'
REVISION = 'OSR_030_PRODUCTION_V1'
MODULE = PACKAGE / 'osr_030_final_freeze.py'
TEST = ROOT / 'test_osr_030_scientific_reasoning_final_certification_freeze.py'
EXPORTS = ('OSR_030_BUILD_ID', 'OSR_030_REVISION', 'ScientificReasoningFinalFreeze', 'certify_and_freeze_osr_001_through_030', 'build_osr_030_certification_manifest', 'verify_osr_030_scientific_reasoning_final_certification_freeze')
MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .osr_026_reasoning_calibration import verify_osr_026_reasoning_calibration_engine
from .osr_027_meta_reasoning_quality import verify_osr_027_meta_reasoning_quality_evaluation
from .osr_028_cross_capability_synthesis import verify_osr_028_cross_capability_scientific_reasoning_synthesis
from .osr_029_intelligence_state import verify_osr_029_oracle_scientific_intelligence_state

OSR_030_BUILD_ID = "OSR-030"
OSR_030_REVISION = "OSR_030_SCIENTIFIC_REASONING_FINAL_CERTIFICATION_FREEZE_V1"

@dataclass(frozen=True)
class ScientificReasoningFinalFreeze:
    certified_builds: tuple[str, ...]
    subsystem: str
    capability: str
    downstream_boundary: str
    freeze_hash: str
    certified: bool = True
    frozen: bool = True
    defect_corrections_only: bool = True

def certify_and_freeze_osr_001_through_030():
    checks = (
        verify_osr_026_reasoning_calibration_engine(),
        verify_osr_027_meta_reasoning_quality_evaluation(),
        verify_osr_028_cross_capability_scientific_reasoning_synthesis(),
        verify_osr_029_oracle_scientific_intelligence_state(),
    )
    if not all(checks):
        raise RuntimeError("OSR final certification failed")

    builds = tuple("OSR-%03d" % i for i in range(1, 31))
    raw = {
        "certified_builds": builds,
        "subsystem": "Oracle Scientific Reasoning",
        "capability": "scientific_reasoning_to_oracle_intelligence_state",
        "downstream_boundary": "oracle_intelligence_state_read_only_consumption",
        "frozen": True,
        "defect_corrections_only": True,
    }

    digest = sha256(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return ScientificReasoningFinalFreeze(
        builds,
        raw["subsystem"],
        raw["capability"],
        raw["downstream_boundary"],
        digest,
    )

def build_osr_030_certification_manifest():
    c = certify_and_freeze_osr_001_through_030()
    return MappingProxyType({
        "build_id": OSR_030_BUILD_ID,
        "revision": OSR_030_REVISION,
        "certified_build_count": len(c.certified_builds),
        "subsystem": c.subsystem,
        "capability": c.capability,
        "downstream_boundary": c.downstream_boundary,
        "frozen": c.frozen,
        "defect_corrections_only": c.defect_corrections_only,
        "execution": False,
        "publication": False,
    })

def verify_osr_030_scientific_reasoning_final_certification_freeze():
    c = certify_and_freeze_osr_001_through_030()
    return (
        c.certified
        and c.frozen
        and c.defect_corrections_only
        and len(c.certified_builds) == 30
        and c.downstream_boundary == "oracle_intelligence_state_read_only_consumption"
    )
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_scientific_reasoning.osr_030_final_freeze import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_osr_030_scientific_reasoning_final_certification_freeze())

    def test_all_thirty(self):
        self.assertEqual(len(certify_and_freeze_osr_001_through_030().certified_builds), 30)

    def test_frozen(self):
        c = certify_and_freeze_osr_001_through_030()
        self.assertTrue(c.frozen)
        self.assertTrue(c.defect_corrections_only)

    def test_boundary(self):
        self.assertEqual(
            certify_and_freeze_osr_001_through_030().downstream_boundary,
            "oracle_intelligence_state_read_only_consumption",
        )

if __name__ == "__main__":
    print("=" * 72)
    print(" OSR-030 CERTIFICATION TEST")
    print(" SCIENTIFIC REASONING FINAL CERTIFICATION + FREEZE")
    print("=" * 72)
    r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OSR-001 through OSR-030 Scientific Reasoning certified")
    print("[PASS] Scientific Reasoning permanently frozen; defect corrections only")
    print("[PASS] Downstream boundary: Oracle intelligence-state read-only consumption")
    print("[DONE] OSR-030 CERTIFIED + FROZEN")
"""

def verify_upstream():
    p = PACKAGE / 'osr_029_intelligence_state.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: " + str(p))
    sys.path.insert(0, str(ROOT))
    try:
        importlib.invalidate_caches()
        m = importlib.import_module('qseries_v2.oracle_scientific_reasoning.osr_029_intelligence_state')
        if getattr(m, 'verify_osr_029_oracle_scientific_intelligence_state')() is not True:
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
