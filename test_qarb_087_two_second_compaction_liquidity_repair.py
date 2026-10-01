import base64
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q


class T(unittest.TestCase):

    def pump_ix(self,n=24,disc=None):
        disc=disc or q.BUY_EXACT_QUOTE_IN_DISC

        return {
            "programId":q.c.PUMP,
            "accounts":[
                {
                    "pubkey":"A%d"%i,
                    "isSigner":False,
                    "isWritable":False,
                }
                for i in range(n)
            ],
            "data":base64.b64encode(
                disc+b"\0"*24
            ).decode(),
        }


    def test_exact_pump_fixed_count(self):
        self.assertEqual(
            q.PUMP_FIXED_ACCOUNTS,
            23
        )


    def test_buy_recognized(self):
        self.assertTrue(
            q.recognized_pump_buy(
                self.pump_ix(
                    23,
                    q.BUY_DISC
                )
            )
        )


    def test_buy_exact_quote_recognized(self):
        self.assertTrue(
            q.recognized_pump_buy(
                self.pump_ix(
                    23,
                    q.BUY_EXACT_QUOTE_IN_DISC
                )
            )
        )


    def test_only_trailing_optional_removed(self):
        ix=self.pump_ix(25)

        z,n=q.trim_optional_pump_accounts(ix)

        self.assertEqual(n,2)

        self.assertEqual(
            len(z["accounts"]),
            23
        )


    def test_fixed_accounts_never_removed(self):
        ix=self.pump_ix(23)

        z,n=q.trim_optional_pump_accounts(ix)

        self.assertIsNone(z)

        self.assertEqual(n,0)


    def test_unknown_pump_instruction_not_trimmed(self):
        ix=self.pump_ix(
            30,
            b"\1\2\3\4\5\6\7\8"
        )

        z,n=q.trim_optional_pump_accounts(ix)

        self.assertIsNone(z)

        self.assertEqual(n,0)


    def test_alt_retry_not_duplicated(self):
        self.assertEqual(
            q.alt_sets([],[]),
            [[]]
        )


    def test_alt_retry_only_when_changed(self):
        self.assertEqual(
            q.alt_sets([],["X"]),
            [[],["X"]]
        )


    def test_size_ladder_descends(self):
        x=q.size_ladder(0.28)

        self.assertEqual(x[0],0.28)

        self.assertEqual(
            x,
            sorted(
                x,
                reverse=True
            )
        )


    def test_exact_086_boundary(self):
        self.assertTrue(
            callable(
                q.q86.memory_candidates
            )
        )

        self.assertTrue(
            callable(
                q.q86.hydrate
            )
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
