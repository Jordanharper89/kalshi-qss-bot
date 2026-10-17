import ast
import unittest
from pathlib import Path

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "checkpoint3_reverse_atomic_compile.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = TARGET.read_text(encoding="utf-8")
        ast.parse(cls.src)

    def test_reverse_direction(self):
        self.assertIn(
            '"METEORA_TO_PUMP"',
            self.src,
        )

    def test_economic_order(self):
        self.assertIn(
            "full = pre + [meteora_ix, pump_ix] + post",
            self.src,
        )

    def test_canonical_compiler(self):
        self.assertIn(
            "r.compile_current(",
            self.src,
        )

    def test_reuses_checkpoint2_hydration(self):
        self.assertIn(
            "checkpoint2_forward_atomic_sim as cp",
            self.src,
        )

    def test_no_simulation(self):
        self.assertNotIn(
            "simulateTransaction",
            self.src,
        )
        self.assertIn(
            "skipped_balance_independent_compile_only",
            self.src,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.src,
        )
        self.assertNotIn(
            ".send(",
            self.src,
        )

    def test_packet_limit(self):
        self.assertIn(
            "REVERSE_COMPILED_TOO_LARGE",
            self.src,
        )
        self.assertIn(
            "1232",
            self.src,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
