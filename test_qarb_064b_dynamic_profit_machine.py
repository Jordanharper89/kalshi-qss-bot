import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064b_dynamic_profit_machine as q


class T(unittest.TestCase):

    def test_mode(self):
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.EXECUTION_AUTHORITY)

    def test_dynamic(self):
        s=inspect.getsource(q.serve)
        self.assertIn("feed.collect",s)
        self.assertIn("_admit",s)
        self.assertIn("capped_valves",s)

    def test_sixdex_base(self):
        self.assertIn(
            "q60b2.prepare_once",
            inspect.getsource(q.serve),
        )

    def test_fresh_paper(self):
        self.assertIn(
            "FreshOnlyPaperLane",
            inspect.getsource(q.serve),
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
