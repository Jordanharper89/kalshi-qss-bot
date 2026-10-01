import struct
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_088_two_second_executable_profit_accounting as q


class T(unittest.TestCase):

    def test_token_amount_decode(self):
        raw=bytearray(165)

        struct.pack_into(
            "<Q",
            raw,
            64,
            123456789
        )

        self.assertEqual(
            q.token_amount_from_data(
                bytes(raw)
            ),
            123456789
        )


    def test_short_token_rejected(self):
        with self.assertRaises(
            RuntimeError
        ):
            q.token_amount_from_data(
                b"\0"*20
            )


    def test_missing_account_zero(self):
        x=q.decode_rpc_account(
            None
        )

        self.assertFalse(
            x["exists"]
        )

        self.assertEqual(
            x["lamports"],
            0
        )


    def test_wsol_not_double_counted(self):
        # 3000 account lamports already include
        # the 2000 wrapped-SOL token amount.
        x=q.wealth_lamports(
            1000,
            {
                "amount":2000,
                "lamports":3000,
            }
        )

        self.assertEqual(
            x,
            4000
        )


    def test_fallback_identity_rejected(self):
        with self.assertRaises(
            RuntimeError
        ):
            q.require_local_identity(
                None,
                "fallback"
            )


    def test_exact_087_compose_reused(self):
        self.assertTrue(
            callable(
                q.q87.compose
            )
        )


    def test_exact_087_candidates_reused(self):
        self.assertTrue(
            callable(
                q.q87.repaired_candidates
            )
        )


    def test_exact_087_compile_reused(self):
        self.assertTrue(
            callable(
                q.q87.compile_candidate
            )
        )


    def test_max_tx_size(self):
        self.assertEqual(
            q.MAX_TX_BYTES,
            1232
        )


    def test_no_broadcast_boundary(self):
        src=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            'c.send(',
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


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
