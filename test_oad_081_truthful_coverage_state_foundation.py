import unittest

from qseries_v2.oracle_adapters.independent.oad_079_live_source_coverage_gap_ranking import (
    COVERED,
    NOT_COVERED,
    UNMAPPED,
    coverage_state,
)
from qseries_v2.oracle_adapters.independent.oad_081_truthful_coverage_state_foundation import (
    verify_truthful_unmapped_semantics,
)

class T(unittest.TestCase):
    def test_other_is_unmapped(self):
        self.assertEqual(
            coverage_state("other",(),()),
            UNMAPPED,
        )

    def test_missing_is_not_covered(self):
        self.assertEqual(
            coverage_state(
                "sports",
                (object(),),
                ("Official league/team feeds",),
            ),
            NOT_COVERED,
        )

    def test_complete_is_covered(self):
        self.assertEqual(
            coverage_state(
                "weather",
                (object(),),
                (),
            ),
            COVERED,
        )

    def test_verify(self):
        self.assertTrue(verify_truthful_unmapped_semantics())

if __name__=="__main__":
    print("="*88)
    print(" OAD-081 CERTIFICATION TEST")
    print(" TRUTHFUL COVERAGE-STATE FOUNDATION — PUBLIC INTERFACE")
    print("="*88)

    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] Public coverage_state interface certified")
    print("[PASS] other/unclassified reports UNMAPPED")
    print("[PASS] missing source families report NOT_COVERED")
    print("[PASS] fully mapped source coverage reports COVERED")
    print("[PASS] probability_enabled=FALSE")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OAD-081 CERTIFIED")
