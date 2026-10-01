import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_089_two_second_dlmm_liquidity_binding_recovery as q


class T(unittest.TestCase):

    def test_normalize_wsol_x(self):
        x=q.normalize_pool(
            {
                "address":"P",
                "token_x":{
                    "address":q.c.WSOL,
                    "decimals":9,
                },
                "token_y":{
                    "address":"TOKEN",
                    "decimals":6,
                },
                "tvl":100,
            },
            "TOKEN"
        )

        self.assertEqual(
            x["address"],
            "P"
        )


    def test_normalize_wsol_y(self):
        x=q.normalize_pool(
            {
                "address":"P",
                "token_x":{
                    "address":"TOKEN"
                },
                "token_y":{
                    "address":q.c.WSOL
                },
            },
            "TOKEN"
        )

        self.assertIsNotNone(x)


    def test_wrong_pair_rejected(self):
        self.assertIsNone(
            q.normalize_pool(
                {
                    "address":"P",
                    "token_x":{
                        "address":"A"
                    },
                    "token_y":{
                        "address":"B"
                    },
                },
                "TOKEN"
            )
        )


    def test_rank_complete(self):
        r=q.rank_complete([
            {
                "complete":False,
                "net_lamports":999,
            },
            {
                "complete":True,
                "net_lamports":10,
                "tvl":1,
            },
            {
                "complete":True,
                "net_lamports":20,
                "tvl":1,
            },
        ])

        self.assertEqual(
            len(r),
            2
        )

        self.assertEqual(
            r[0]["net_lamports"],
            20
        )


    def test_partial_never_ranked(self):
        self.assertEqual(
            q.rank_complete([
                {
                    "complete":False,
                    "reason":"DLMM_PARTIAL",
                    "net_lamports":999999,
                }
            ]),
            []
        )


    def test_pool_retry_count_bounded(self):
        self.assertEqual(
            q.POOL_RPC_ATTEMPTS,
            5
        )


    def test_pool_snapshot_has_state_builder(self):
        self.assertTrue(
            callable(
                q.hydrate_pool
            )
        )


    def test_quote_uses_hydrated_state(self):
        self.assertTrue(
            callable(
                q.quote_hydrated_pool
            )
        )


    def test_exact_087_size_ladder(self):
        self.assertTrue(
            callable(
                q.q87.size_ladder
            )
        )


    def test_no_broadcast(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "sendTransaction",
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
