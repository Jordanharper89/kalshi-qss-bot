import inspect
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as q
)


class T(unittest.TestCase):

    def test_start_retry_installed(self):
        src=inspect.getsource(
            type(q.BLOCKHASH).start
        )

        self.assertIn(
            "SAE008C_BLOCKHASH_RETRY",
            src
        )

        self.assertIn(
            "range(1,7)",
            src.replace(" ","")
        )

    def test_account_audit_preserved(self):
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
            qarb_087_two_second_compaction_liquidity_repair as q87
        )

        src=inspect.getsource(
            q87.repaired_candidates
        )

        self.assertIn(
            "SAE008B_CANDIDATE",
            src
        )

    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )

    def test_no_broadcast(self):
        src=inspect.getsource(q)

        self.assertNotIn(
            "sendTransaction",
            src
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
