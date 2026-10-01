import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_001_live_solana_executor as q
)


class T(unittest.TestCase):

    def test_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )

        self.assertTrue(
            q.ORACLE_EXECUTION_AUTHORITY
        )


    def test_exact_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )

        self.assertEqual(
            q.MICRO_SOL,
            0.001
        )


    def test_oracle_arm(self):
        s=inspect.getsource(
            q.armed
        )

        self.assertIn(
            "ORACLE_SOLANA_EXECUTION_ARM",
            s
        )


    def test_signed_sim_before_send_exists(self):
        self.assertTrue(
            callable(
                q.signed_simulation
            )
        )

        self.assertTrue(
            callable(
                q.send_once
            )
        )


    def test_send_once_no_retry(self):
        s=inspect.getsource(
            q.send_once
        )

        self.assertIn(
            '"maxRetries":0',
            s
        )


    def test_preflight_enabled(self):
        s=inspect.getsource(
            q.send_once
        )

        self.assertIn(
            '"skipPreflight":False',
            s
        )


    def test_funding_gate(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "minimum_balance=2_000_000",
            s
        )

        self.assertIn(
            "INSUFFICIENT_EXECUTION_BALANCE",
            s
        )


    def test_oracle_runtime_state(self):
        self.assertIn(
            "runtime_state\\oracle",
            str(q.STATE)
        )


    def test_no_qseries_execution_owner(self):
        self.assertNotEqual(
            q.EXECUTION_OWNER,
            "Q_SERIES"
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
