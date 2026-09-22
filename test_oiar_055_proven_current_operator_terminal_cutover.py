import inspect
import unittest

import qseries_v2.oracle_intelligence_analytics_runtime.oiar_055_proven_current_operator_terminal_cutover as m


class T(unittest.TestCase):

    def test_identity(self):
        self.assertEqual(
            m.OIAR_055_BUILD_ID,
            "OIAR-055",
        )

    def test_queries(self):
        self.assertTrue(
            m.is_current_trader_query(
                "what are the plays for today?"
            )
        )

        self.assertTrue(
            m.is_current_trader_query(
                "what do you like right now?"
            )
        )

    def test_no_canonical_scan(self):
        self.assertNotIn(
            "oracle_canonical_observations",
            inspect.getsource(m),
        )


if __name__ == "__main__":

    print("=" * 88)
    print(" OIAR-055 CERTIFICATION TEST")
    print(" PROVEN CURRENT OPERATOR TERMINAL CUTOVER")
    print("=" * 88)

    r = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print(
        "[PASS] snapshot-only current trader terminal "
        "cutover certified"
    )
    print("[DONE] OIAR-055 CERTIFIED")
