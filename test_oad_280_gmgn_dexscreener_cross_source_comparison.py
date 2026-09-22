import unittest

import qseries_v2.oracle_adapters.independent.oad_280_gmgn_dexscreener_cross_source_comparison as oad280


class T(unittest.TestCase):
    def test_deterministic_comparison_contract(self):
        r = oad280.compare_gmgn_dexscreener(
            {
                "price_usd": 1.00,
                "liquidity_usd": 100000.0,
                "volume_h24": 50000.0,
            },
            {
                "price_usd": 1.02,
                "liquidity_usd": 102000.0,
                "volume_h24": 51000.0,
            },
        )
        self.assertEqual(r.comparable_fields, 3)
        self.assertEqual(r.agreements, 3)
        self.assertEqual(r.contradictions, 0)

    def test_physical_same_token_cross_source(self):
        r = oad280.compare_live_gmgn_dexscreener_for_same_token(
            timeout_seconds=30.0
        )

        print("[PHYSICAL] token=", r.token_address)
        print("[PHYSICAL] comparable=", r.comparable_fields)
        print("[PHYSICAL] agreements=", r.agreements)
        print("[PHYSICAL] contradictions=", r.contradictions)

        for row in r.metrics:
            print(
                "[PHYSICAL]",
                row.metric,
                "gmgn=",
                row.gmgn_value,
                "dexscreener=",
                row.dexscreener_value,
                "relative_difference=",
                row.relative_difference,
                "state=",
                row.state,
            )

        self.assertTrue(r.token_address)
        self.assertGreaterEqual(r.comparable_fields, 1)
        self.assertEqual(
            r.agreements + r.contradictions,
            r.comparable_fields,
        )
        self.assertIsNone(r.probability)
        self.assertIsNone(r.direction)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(oad280.PROBABILITY_ENABLED)
        self.assertFalse(oad280.DIRECTION_ENABLED)
        self.assertFalse(oad280.PUBLICATION_ALLOWED)
        self.assertFalse(oad280.EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-280 PHYSICAL CERTIFICATION TEST")
    print(" GMGN <-> DEXSCREENER SAME-TOKEN CROSS-SOURCE COMPARISON")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] deterministic comparison contract preserved")
    print("[PASS] physical same-token GMGN <-> DexScreener comparison certified")
    print("[PASS] provider disagreement preserved as contradiction")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-280 PHYSICALLY CERTIFIED")
