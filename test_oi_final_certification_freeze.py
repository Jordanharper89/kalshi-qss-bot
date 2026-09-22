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
