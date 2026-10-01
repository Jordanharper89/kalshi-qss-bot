from pathlib import Path
import unittest

class T(unittest.TestCase):

    def test_candidate_audit(self):
        p=Path(
            "qseries_v2/oracle_strategy_intelligence/"
            "solana_money/qarb_execution_engineering/"
            "qarb_087_two_second_compaction_liquidity_repair.py"
        )
        s=p.read_text(encoding="utf-8")
        self.assertIn("[SAE008B_CANDIDATE]",s)
        self.assertIn("[SAE008B_ACCOUNT]",s)

    def test_boundary_preserved(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q
        self.assertEqual(q.PUMP_FIXED_ACCOUNTS,26)

if __name__=="__main__":
    unittest.main(verbosity=2)
