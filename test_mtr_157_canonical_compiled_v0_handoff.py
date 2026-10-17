import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_157_canonical_compiled_v0_handoff as m

class Tests(unittest.TestCase):
    def test_exact_runtime_exists(self):
        self.assertTrue(m.RUNTIME.is_file())
    def test_compiler_functions_identified(self):
        self.assertTrue(m.contract())
    def test_malformed_transaction_rejected(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "tx.txt"
            p.write_text("Zm9v", encoding="ascii")
            with self.assertRaises((ValueError, TypeError, IndexError, KeyError)):
                m.verify_file(p)
    def test_no_execution_side_effects(self):
        self.assertNotIn("private_key", m.contract.__code__.co_names)
        self.assertEqual(len(m.CANONICAL), 44)
if __name__ == "__main__":
    unittest.main(verbosity=2)
