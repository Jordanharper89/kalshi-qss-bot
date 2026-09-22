from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BUILD_ID = "OI-FINAL"
REVISION = "OI_FINAL_CERTIFICATION_FREEZE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_intelligence"
FREEZE = PKG / "oi_final_certification_freeze.py"
MANIFEST = PKG / "OI_FINAL_FREEZE_MANIFEST.json"
FINAL_TEST = ROOT / "test_oi_final_certification_freeze.py"

FIRST = 1
LAST = 66
MOD_RE = re.compile(r"^oi_(\d{3})_.*\.py$", re.I)
TEST_RE = re.compile(r"^test_oi_(\d{3})_.*\.py$", re.I)

FREEZE_SOURCE = """
from __future__ import annotations

BUILD_ID = "OI-FINAL"
REVISION = "OI_FINAL_CERTIFICATION_FREEZE_V1"
STATUS = "COMPLETE_CERTIFIED_PERMANENTLY_FROZEN"

READ_ONLY = True
DEFECT_CORRECTIONS_ONLY = True
ARCHITECTURAL_EXPANSION_ALLOWED = False
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False

def verify_observation_intelligence_final_freeze() -> bool:
    assert STATUS == "COMPLETE_CERTIFIED_PERMANENTLY_FROZEN"
    assert READ_ONLY is True
    assert DEFECT_CORRECTIONS_ONLY is True
    assert ARCHITECTURAL_EXPANSION_ALLOWED is False
    assert NETWORK_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert EXECUTION_ALLOWED is False
    assert QSERIES_EXECUTION_ALLOWED is False
    return True
""".lstrip()

FINAL_TEST_SOURCE = """
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from qseries_v2.observation_intelligence.oi_final_certification_freeze import (
    STATUS,
    READ_ONLY,
    DEFECT_CORRECTIONS_ONLY,
    ARCHITECTURAL_EXPANSION_ALLOWED,
    NETWORK_ALLOWED,
    PERSISTENCE_ALLOWED,
    PUBLICATION_ALLOWED,
    EXECUTION_ALLOWED,
    QSERIES_EXECUTION_ALLOWED,
    verify_observation_intelligence_final_freeze,
)

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2" / "observation_intelligence"
MANIFEST = PKG / "OI_FINAL_FREEZE_MANIFEST.json"

class TestOIFinalFreeze(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(
            verify_observation_intelligence_final_freeze()
        )

    def test_status(self):
        self.assertEqual(
            STATUS,
            "COMPLETE_CERTIFIED_PERMANENTLY_FROZEN",
        )

    def test_policy(self):
        self.assertTrue(READ_ONLY)
        self.assertTrue(DEFECT_CORRECTIONS_ONLY)
        self.assertFalse(ARCHITECTURAL_EXPANSION_ALLOWED)
        self.assertFalse(NETWORK_ALLOWED)
        self.assertFalse(PERSISTENCE_ALLOWED)
        self.assertFalse(PUBLICATION_ALLOWED)
        self.assertFalse(EXECUTION_ALLOWED)
        self.assertFalse(QSERIES_EXECUTION_ALLOWED)

    def test_manifest(self):
        data = json.loads(
            MANIFEST.read_text(encoding="utf-8")
        )
        self.assertEqual(
            data["certified_range"],
            "OI-001..OI-066",
        )
        self.assertEqual(
            data["module_count"],
            66,
        )
        self.assertEqual(
            data["test_count"],
            66,
        )

    def test_frozen_hashes(self):
        data = json.loads(
            MANIFEST.read_text(encoding="utf-8")
        )
        for relative, expected in data["source_hashes"].items():
            path = ROOT / relative
            self.assertTrue(path.is_file())
            actual = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            self.assertEqual(
                actual,
                expected,
                msg=f"Frozen OI source changed: {relative}",
            )

if __name__ == "__main__":
    print("=" * 72)
    print(" OI FINAL CERTIFICATION TEST")
    print(" OBSERVATION INTELLIGENCE PERMANENT FREEZE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOIFinalFreeze
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] OI-001 through OI-066 frozen")
    print("[PASS] Final source hashes verified")
    print("[PASS] Read-only boundary preserved")
    print("[PASS] Defect corrections only")
    print("[PASS] Architectural expansion disabled")
    print("[DONE] OBSERVATION INTELLIGENCE PERMANENTLY FROZEN")
""".lstrip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_path(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path))
    compile(source, str(path), "exec")


def discover(pattern: re.Pattern[str], paths) -> dict[int, Path]:
    found: dict[int, list[Path]] = {}

    for path in sorted(paths):
        match = pattern.match(path.name)
        if match is None:
            continue

        number = int(match.group(1))
        if FIRST <= number <= LAST:
            found.setdefault(number, []).append(path)

    duplicates = {
        number: values
        for number, values in found.items()
        if len(values) != 1
    }

    if duplicates:
        detail = "; ".join(
            f"OI-{number:03d}: "
            + ", ".join(path.name for path in values)
            for number, values in sorted(duplicates.items())
        )
        raise RuntimeError(
            "Duplicate OI artifacts discovered: " + detail
        )

    return {
        number: values[0]
        for number, values in found.items()
    }


def require_complete(found: dict[int, Path], label: str) -> None:
    missing = [
        number
        for number in range(FIRST, LAST + 1)
        if number not in found
    ]

    if missing:
        raise RuntimeError(
            f"{label} missing: "
            + ", ".join(
                f"OI-{number:03d}"
                for number in missing
            )
        )


def main() -> int:
    print("=" * 72)
    print(" OI FINAL CERTIFICATION / FREEZE INSTALLER")
    print(" OBSERVATION INTELLIGENCE")
    print("=" * 72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")

    if not PKG.is_dir():
        raise RuntimeError(
            f"Observation Intelligence package missing: {PKG}"
        )

    modules = discover(
        MOD_RE,
        PKG.glob("oi_*.py"),
    )
    tests = discover(
        TEST_RE,
        ROOT.glob("test_oi_*.py"),
    )

    require_complete(
        modules,
        "Certified OI modules",
    )
    require_complete(
        tests,
        "OI certification tests",
    )

    print("[PASS] Exact OI-001 through OI-066 module range found")
    print("[PASS] Exact OI-001 through OI-066 test range found")

    for number in range(FIRST, LAST + 1):
        compile_path(modules[number])
        compile_path(tests[number])

    print("[PASS] All OI modules and tests compile")

    before = {
        path.relative_to(ROOT).as_posix(): sha(path)
        for path in modules.values()
    }

    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"

    print("[RUN] Full OI certification suite")

    for number in range(FIRST, LAST + 1):
        test = tests[number]

        result = subprocess.run(
            [sys.executable, str(test)],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if result.returncode != 0:
            print(result.stdout)
            raise RuntimeError(
                f"OI-{number:03d} certification failed: {test.name}"
            )

        print(f"[PASS] OI-{number:03d}")

    after = {
        path.relative_to(ROOT).as_posix(): sha(path)
        for path in modules.values()
    }

    if before != after:
        raise RuntimeError(
            "Certified OI source changed during certification"
        )

    print("[PASS] Full OI-001 through OI-066 suite passed")
    print("[PASS] Certified OI source remained unchanged")

    ast.parse(
        FREEZE_SOURCE,
        filename=str(FREEZE),
    )
    ast.parse(
        FINAL_TEST_SOURCE,
        filename=str(FINAL_TEST),
    )

    manifest = {
        "build_id": BUILD_ID,
        "revision": "OI_FINAL_CERTIFICATION_FREEZE_V1",
        "status": "COMPLETE_CERTIFIED_PERMANENTLY_FROZEN",
        "certified_range": "OI-001..OI-066",
        "module_count": 66,
        "test_count": 66,
        "read_only": True,
        "defect_corrections_only": True,
        "architectural_expansion_allowed": False,
        "network_allowed": False,
        "persistence_allowed": False,
        "publication_allowed": False,
        "execution_allowed": False,
        "qseries_execution_allowed": False,
        "source_hashes": after,
    }

    affected = (FREEZE, MANIFEST, FINAL_TEST)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        FREEZE.write_text(
            FREEZE_SOURCE,
            encoding="utf-8",
            newline="\n",
        )
        MANIFEST.write_text(
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        FINAL_TEST.write_text(
            FINAL_TEST_SOURCE,
            encoding="utf-8",
            newline="\n",
        )

        compile_path(FREEZE)
        compile_path(FINAL_TEST)

        print("[PASS] Wrote final freeze module")
        print("[PASS] Wrote final freeze manifest")
        print("[PASS] Wrote final freeze certification test")

        result = subprocess.run(
            [sys.executable, str(FINAL_TEST)],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        print(result.stdout)

        if result.returncode != 0:
            raise RuntimeError(
                "OI final freeze certification failed"
            )

        final_hash = hashlib.sha256(
            FREEZE.read_bytes()
            + MANIFEST.read_bytes()
            + FINAL_TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic final freeze hash: {final_hash}"
        )
        print(
            "[PASS] Observation Intelligence is COMPLETE, "
            "CERTIFIED, and PERMANENTLY FROZEN"
        )
        print(
            "[PASS] Future OI changes restricted to genuine defect corrections"
        )
        print(
            "[PASS] New live sources must enter through the separate "
            "observation-adapter subsystem"
        )
        print("[DONE] OI FINAL FREEZE COMPLETE")

        return 0

    except Exception:
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(original)

        print(
            "[ROLLBACK] OI final freeze failed; freeze artifacts restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
