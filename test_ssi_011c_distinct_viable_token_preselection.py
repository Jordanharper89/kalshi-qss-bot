import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_011_physical_multi_token_cohort import discover_distinct_viable_tokens

class T(unittest.TestCase):
    def test_preselection(self):
        viable,rejected,discovered=discover_distinct_viable_tokens(
            required=5
        )

        print(
            "[SSI-011C-PRESELECT]",
            "discovered=",discovered,
            "viable=",viable,
            "rejected=",rejected,
        )

        self.assertGreaterEqual(len(viable),5)
        self.assertEqual(len(viable),len(set(viable)))

if __name__=="__main__":
    unittest.main(verbosity=2)
