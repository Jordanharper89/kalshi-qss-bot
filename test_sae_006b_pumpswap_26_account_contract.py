import base64
import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair
    as q
)

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as c
)


class T(unittest.TestCase):

    def test_26_account_contract(self):
        self.assertEqual(
            q.PUMP_FIXED_ACCOUNTS,
            26
        )

    def test_exact_quote_buy_recognized(self):
        ix={
            "programId":q.c.PUMP,
            "data":base64.b64encode(
                q.BUY_EXACT_QUOTE_IN_DISC
                +b"\x00"*16
            ).decode(),
            "accounts":[],
        }

        self.assertTrue(
            q.recognized_pump_buy(ix)
        )

    def test_first_26_preserved(self):
        accounts=[
            {
                "pubkey":"ACCOUNT_"+str(i),
                "isSigner":False,
                "isWritable":False,
            }
            for i in range(28)
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
            26
        )

        self.assertEqual(
            removed,
            2
        )

        self.assertEqual(
            trimmed["accounts"][23]["pubkey"],
            "ACCOUNT_23"
        )

        self.assertEqual(
            trimmed["accounts"][24]["pubkey"],
            "ACCOUNT_24"
        )

        self.assertEqual(
            trimmed["accounts"][25]["pubkey"],
            "ACCOUNT_25"
        )

    def test_exact_26_not_trimmed(self):
        accounts=[
            {
                "pubkey":"ACCOUNT_"+str(i),
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

        self.assertIsNone(trimmed)
        self.assertEqual(removed,0)

    def test_sae003_preserved(self):
        self.assertEqual(
            c.q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_size_curve_preserved(self):
        src=inspect.getsource(
            c.exact_best
        )

        for size in (
            "0.001",
            "0.010",
            "0.025",
            "0.050",
            "0.100",
            "0.180",
            "0.280",
            "0.500",
            "1.000",
            "1.400",
        ):
            self.assertIn(size,src)

    def test_safety(self):
        self.assertFalse(
            c.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            c.PAPER_ONLY
        )

        self.assertFalse(
            c.REAL_MONEY_MOVED
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            inspect.getsource(c)
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
