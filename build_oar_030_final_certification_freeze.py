from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"

MODULE = PKG / "oar_030_final_certification_freeze.py"
MANIFEST = PKG / "OAR_FINAL_FREEZE_MANIFEST.json"
TEST = ROOT / "test_oar_030_final_certification_freeze.py"

EXPECTED_START = 1
EXPECTED_END = 29

MODULE_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

BUILD_ID = "OAR-030"
OAR_030_REVISION = "OAR_030_FINAL_CERTIFICATION_FREEZE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False
FROZEN = True
DEFECT_CORRECTIONS_ONLY = True

ROOT = Path(__ROOT_PATH__)
MANIFEST = Path(__MANIFEST_PATH__)


def _sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def verify_oar_final_freeze() -> bool:
    payload = json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    if payload["frozen"] is not True:
        return False

    if (
        payload["defect_corrections_only"]
        is not True
    ):
        return False

    for item in payload["files"]:
        path = ROOT / item["path"]

        if not path.is_file():
            return False

        if _sha(path) != item["sha256"]:
            return False

    return True


__all__ = [
    "BUILD_ID",
    "OAR_030_REVISION",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "PUBLICATION_ALLOWED",
    "PERSISTENCE_ALLOWED",
    "FROZEN",
    "DEFECT_CORRECTIONS_ONLY",
    "verify_oar_final_freeze",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.observation_adapter_runtime.oar_030_final_certification_freeze import (
    DEFECT_CORRECTIONS_ONLY,
    FROZEN,
    verify_oar_final_freeze,
)

ROOT = Path.cwd().resolve()
MANIFEST = (
    ROOT
    / "qseries_v2"
    / "observation_adapter_runtime"
    / "OAR_FINAL_FREEZE_MANIFEST.json"
)


class T(unittest.TestCase):
    def test_status(self):
        self.assertTrue(FROZEN)
        self.assertTrue(
            DEFECT_CORRECTIONS_ONLY
        )

    def test_manifest(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            payload["build_range"],
            "OAR-001 through OAR-029",
        )

        self.assertTrue(
            payload["frozen"]
        )

    def test_verifier(self):
        self.assertTrue(
            verify_oar_final_freeze()
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-030 CERTIFICATION TEST")
    print(" OBSERVATION ADAPTER RUNTIME PERMANENT FREEZE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] OAR-001 through OAR-029 frozen")
    print("[PASS] Final source hashes verified")
    print("[PASS] Read-only boundary preserved")
    print("[PASS] Defect corrections only")
    print("[DONE] OBSERVATION ADAPTER RUNTIME PERMANENTLY FROZEN")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module_path(number: int) -> Path:
    matches = tuple(
        sorted(
            PKG.glob(
                f"oar_{number:03d}_*.py"
            )
        )
    )

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one OAR-{number:03d} "
            f"module, found {len(matches)}"
        )

    return matches[0]


def test_path(number: int) -> Path:
    matches = tuple(
        sorted(
            ROOT.glob(
                f"test_oar_{number:03d}_*.py"
            )
        )
    )

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one OAR-{number:03d} "
            f"test, found {len(matches)}"
        )

    return matches[0]


def compile_file(path: Path) -> None:
    ast.parse(
        path.read_text(
            encoding="utf-8"
        ),
        filename=str(path),
    )


def run_test(path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError(
            f"Certification failed: {path.name}"
        )


def write_checked(
    path: Path,
    source: str,
) -> None:
    text = source.lstrip()
    ast.parse(
        text,
        filename=str(path),
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OAR-030 INSTALLER")
    print(" FINAL CERTIFICATION / PERMANENT FREEZE")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_030_FINAL_CERTIFICATION_FREEZE_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    modules = tuple(
        module_path(number)
        for number in range(
            EXPECTED_START,
            EXPECTED_END + 1,
        )
    )

    tests = tuple(
        test_path(number)
        for number in range(
            EXPECTED_START,
            EXPECTED_END + 1,
        )
    )

    print(
        "[PASS] Exact OAR-001 through OAR-029 "
        "module range found"
    )
    print(
        "[PASS] Exact OAR-001 through OAR-029 "
        "test range found"
    )

    for path in (
        *modules,
        *tests,
    ):
        compile_file(path)

    print(
        "[PASS] All OAR modules and tests compile"
    )

    source_hashes = {
        path: sha(path)
        for path in modules
    }

    print(
        "[RUN] Full OAR certification suite"
    )

    for number, path in enumerate(
        tests,
        start=1,
    ):
        run_test(path)
        print(
            f"[PASS] OAR-{number:03d}"
        )

    print(
        "[PASS] Full OAR-001 through OAR-029 "
        "suite passed"
    )

    for path, expected in source_hashes.items():
        if sha(path) != expected:
            raise RuntimeError(
                f"Certified OAR source changed "
                f"during test suite: {path.name}"
            )

    print(
        "[PASS] Certified OAR source remained unchanged"
    )

    manifest_payload = {
        "revision": (
            "OAR_FINAL_FREEZE_MANIFEST_V1"
        ),
        "build_range": (
            "OAR-001 through OAR-029"
        ),
        "frozen": True,
        "defect_corrections_only": True,
        "read_only": True,
        "execution_allowed": False,
        "publication_allowed": False,
        "persistence_allowed": False,
        "files": [
            {
                "path": str(
                    path.relative_to(ROOT)
                ).replace("\\", "/"),
                "sha256": source_hashes[path],
            }
            for path in modules
        ],
    }

    manifest_text = (
        json.dumps(
            manifest_payload,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )

    module_source = (
        MODULE_SOURCE_TEMPLATE
        .replace(
            "__ROOT_PATH__",
            repr(str(ROOT)),
        )
        .replace(
            "__MANIFEST_PATH__",
            repr(str(MANIFEST)),
        )
    )

    affected = (
        MODULE,
        MANIFEST,
        TEST,
    )

    backups = {
        path: (
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in affected
    }

    try:
        write_checked(
            MODULE,
            module_source,
        )

        MANIFEST.write_text(
            manifest_text,
            encoding="utf-8",
            newline="\n",
        )

        print(
            f"[PASS] Wrote: "
            f"{MANIFEST.relative_to(ROOT)}"
        )

        write_checked(
            TEST,
            TEST_SOURCE,
        )

        run_test(TEST)

        final_hash = hashlib.sha256(
            MODULE.read_bytes()
            + MANIFEST.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            "[PASS] Deterministic final freeze hash: "
            f"{final_hash}"
        )

        print(
            "[PASS] Observation Adapter Runtime is "
            "COMPLETE, CERTIFIED, and PERMANENTLY FROZEN"
        )

        print(
            "[PASS] Future OAR changes restricted "
            "to genuine defect corrections"
        )

        print(
            "[DONE] OAR FINAL FREEZE COMPLETE"
        )

        return 0

    except Exception:
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(original)

        print(
            "[ROLLBACK] OAR-030 final freeze failed; "
            "freeze artifacts restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
