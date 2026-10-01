import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair as q
)


class T(unittest.TestCase):

    def test_pump_trim_disabled(self):
        accounts=[
            {
                "pubkey":"ACCOUNT_%d"%i,
                "isSigner":False,
                "isWritable":False,
            }
            for i in range(40)
        ]

        import base64

        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC+b"\x00"*16
            ).decode(),
            "accounts":accounts,
        }

        trimmed,removed=q.trim_optional_pump_accounts(ix)

        self.assertIsNone(trimmed)
        self.assertEqual(removed,0)

    def test_no_slice_semantics(self):
        src=inspect.getsource(
            q.trim_optional_pump_accounts
        )

        self.assertNotIn(
            "PUMP_FIXED_ACCOUNTS]",
            src
        )

        self.assertIn(
            "Preserve the instruction exactly",
            src
        )

    def test_execution_stays_disabled(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.REAL_MONEY_MOVED)


if __name__=="__main__":
    unittest.main(verbosity=2)
