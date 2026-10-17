import unittest
from pathlib import Path

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "canonical_alt_coverage_diagnostic.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = TARGET.read_text(encoding="utf-8")

    def test_canonical_only(self):
        self.assertIn("solana_atomic_executor", str(TARGET))
        self.assertIn("canonical_alt.json", self.s)
        self.assertIn("checkpoint2_forward_atomic_sim", self.s)

    def test_no_mutation_or_broadcast(self):
        forbidden = (
            "ORACLE_CANONICAL_ALT_CREATE",
            "create_lookup_table",
            "extend_lookup_table",
            "sendTransaction",
            ".send(",
        )
        for needle in forbidden:
            self.assertNotIn(needle, self.s)

    def test_exact_projection_contract(self):
        self.assertIn("MAX_TX_BYTES = 1232", self.s)
        self.assertIn("_compile_size_with_synthetic_alt", self.s)
        self.assertIn("strategy_a_pass", self.s)
        self.assertIn("STATIC_SHARED_CANDIDATE", self.s)
        self.assertIn("PAIR_SPECIFIC", self.s)

    def test_report_contract(self):
        self.assertIn(
            "canonical_alt_coverage_diagnostic.json",
            self.s,
        )
        self.assertIn("mutation_performed", self.s)
        self.assertIn("False", self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
