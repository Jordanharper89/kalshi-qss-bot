from __future__ import annotations

import unittest
from pathlib import Path

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_068_canonical_evidence_index_identity_divergence_physical_proof import (
    physical_probe,
    verify_oiar_068_contract,
)


ROOT = Path.cwd().resolve()


class T(unittest.TestCase):

    def test_verifier(self):
        self.assertTrue(verify_oiar_068_contract())

    def test_physical_divergence(self):
        x = physical_probe(ROOT)

        self.assertGreater(
            x["sampled_missing_settlements"],
            0,
        )

        self.assertTrue(
            x["index_name"],
        )

        self.assertTrue(
            x["exact_canonical_lookup_uses_index"],
        )

        classified = (
            x["canonical_present_evidence_missing"]
            + x["canonical_no_exact_ticker"]
            + x["evidence_exact_ticker_found"]
        )

        self.assertGreater(
            classified,
            0,
        )

        self.assertTrue(x["read_only"])
        self.assertEqual(x["repaired_rows"], 0)
        self.assertFalse(x["probability_enabled"])
        self.assertFalse(x["execution_authority"])


if __name__ == "__main__":
    print("=" * 88)
    print(" OIAR-068 CERTIFICATION TEST")
    print(" CANONICAL / EVIDENCE-INDEX IDENTITY DIVERGENCE PHYSICAL PROOF")
    print("=" * 88)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(T)
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] missing-settlement canonical identity physically classified")
    print("[PASS] canonical/evidence-index divergence physically measured")
    print("[PASS] exact canonical identity lookup uses proven index")
    print("[PASS] no learning state repaired or modified")
    print("[PASS] probability remains gated")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-068 CERTIFIED")
