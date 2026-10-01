import base64
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair
    as q
)


class T(unittest.TestCase):

    def test_current_fixed_account_count(self):
        self.assertEqual(
            q.PUMP_FIXED_ACCOUNTS,
            24
        )

    def test_buy_exact_quote_in_recognized(self):
        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC
                +b"\x00"*16
            ).decode(),
            "accounts":[
                {
                    "pubkey":
                        "X"+str(i),
                    "isSigner":False,
                    "isWritable":False,
                }
                for i in range(26)
            ],
        }

        self.assertTrue(
            q.recognized_pump_buy(ix)
        )

    def test_pool_v2_account_is_preserved(self):
        accounts=[
            {
                "pubkey":
                    "ACCOUNT_"+str(i),
                "isSigner":False,
                "isWritable":False,
            }
            for i in range(26)
        ]

        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC
                +b"\x00"*16
            ).decode(),
            "accounts":accounts,
        }

        trimmed,removed=(
            q.trim_optional_pump_accounts(ix)
        )

        self.assertIsNotNone(trimmed)

        self.assertEqual(
            len(trimmed["accounts"]),
            24
        )

        self.assertEqual(
            removed,
            2
        )

        #
        # Account index 23 = physical
        # account #24. This was previously
        # being stripped by the stale
        # 23-account boundary.
        #
        self.assertEqual(
            trimmed["accounts"][23]["pubkey"],
            "ACCOUNT_23"
        )

    def test_only_accounts_after_24_removed(self):
        accounts=[
            {
                "pubkey":
                    "ACCOUNT_"+str(i),
                "isSigner":False,
                "isWritable":False,
            }
            for i in range(26)
        ]

        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC
                +b"\x00"*16
            ).decode(),
            "accounts":accounts,
        }

        trimmed,_=q.trim_optional_pump_accounts(ix)

        kept=[
            x["pubkey"]
            for x in trimmed["accounts"]
        ]

        self.assertIn(
            "ACCOUNT_23",
            kept
        )

        self.assertNotIn(
            "ACCOUNT_24",
            kept
        )

        self.assertNotIn(
            "ACCOUNT_25",
            kept
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


if __name__=="__main__":
    unittest.main(verbosity=2)
