import ast
import unittest
from pathlib import Path

PKG=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor"
)

class T(unittest.TestCase):
    def test_module(self):
        from qseries_v2.oracle_execution.solana_atomic_executor import mry_010_live_promotion as m

        self.assertEqual(
            m.MAX_ADMISSIONS_PER_ROTATION,
            2,
        )

        self.assertTrue(
            callable(m.admit_batch)
        )

    def test_activation(self):
        src=(
            PKG/
            "mry_005_runtime_activation.py"
        ).read_text(
            encoding="utf-8"
        )

        ast.parse(src)

        self.assertIn(
            "mry_010_live_promotion",
            src,
        )

        self.assertIn(
            "m10.admit_batch(",
            src,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
