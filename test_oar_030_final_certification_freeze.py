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
