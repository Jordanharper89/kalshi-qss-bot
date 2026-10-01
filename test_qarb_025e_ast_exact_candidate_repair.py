import inspect
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_024_existing_python_atomic_source_bridge as b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_025e_ast_exact_candidate_repair as r

class T(unittest.TestCase):
    def test_bridge_delegates_exact_source(self):
        src = inspect.getsource(b.candidate_instruction_sets)
        self.assertIn("load_source().candidate_instruction_sets(route)", src)
        print("[PASS] bridge delegates to exact qsb059 candidate_instruction_sets")

    def test_single_size_default(self):
        self.assertEqual(r.SIZES, (0.5,))
        print("[PASS] one-size default avoids HTTP hammering")

    def test_execution_false(self):
        self.assertIs(r.execution_authority, False)
        print("[PASS] execution_authority=FALSE")

if __name__ == "__main__":
    unittest.main(verbosity=2)
