import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_094_execution_shadow_stability_certification as q


class T(unittest.TestCase):

    def active(self,bps=100,bytes_=1158):
        return {
            "status":
                "CURRENT_EXECUTION_SHADOW_PASS",

            "active":{
                "fresh_net_bps":
                    bps,

                "fresh_net_lamports":
                    1000,

                "candidate":
                    "C",

                "transaction_bytes":
                    bytes_,

                "size_sol":
                    1.4,

                "sim_err":
                    None,

                "pump_pool":
                    "P",

                "meteora_meta":{
                    "address":"M"
                },
            },

            "simulation":{
                "preferred_reused":
                    True
            },
        }


    def cycle(self,n,result):
        return {
            "cycle":n,
            "results":{
                "T":result
            }
        }


    def test_three_clean_cycles_certify(self):
        h=[
            self.cycle(1,self.active(100)),
            self.cycle(2,self.active(120)),
            self.cycle(3,self.active(110)),
        ]

        x=q.analyze_token(
            "T",
            h
        )

        self.assertTrue(
            x[
                "certified_stable_shadow"
            ]
        )


    def test_partial_cycle_not_certified(self):
        h=[
            self.cycle(1,self.active()),
            self.cycle(
                2,
                {
                    "status":
                        "CURRENTLY_INACTIVE",
                    "revalidation":{
                        "reason":
                            "DLMM_PARTIAL"
                    },
                }
            ),
            self.cycle(3,self.active()),
        ]

        x=q.analyze_token(
            "T",
            h
        )

        self.assertFalse(
            x[
                "certified_stable_shadow"
            ]
        )


    def test_reentry_count(self):
        obs=[
            {"active":True},
            {"active":False},
            {"active":True},
        ]

        x=q.transitions(obs)

        self.assertEqual(
            x[
                "drop_count"
            ],
            1
        )

        self.assertEqual(
            x[
                "reentry_count"
            ],
            1
        )


    def test_candidate_instability_blocks(self):
        h=[
            self.cycle(1,self.active()),
            self.cycle(2,self.active()),
            self.cycle(3,self.active()),
        ]

        h[2][
            "results"
        ][
            "T"
        ][
            "active"
        ][
            "candidate"
        ]="OTHER"

        x=q.analyze_token(
            "T",
            h
        )

        self.assertFalse(
            x[
                "certified_stable_shadow"
            ]
        )


    def test_tx_size_instability_blocks(self):
        h=[
            self.cycle(1,self.active(bytes_=1158)),
            self.cycle(2,self.active(bytes_=1190)),
            self.cycle(3,self.active(bytes_=1158)),
        ]

        x=q.analyze_token(
            "T",
            h
        )

        self.assertFalse(
            x[
                "certified_stable_shadow"
            ]
        )


    def test_exact_093_history(self):
        self.assertTrue(
            str(
                q.q93.HISTORY
            ).endswith(
                "qarb_093_execution_shadow_history.jsonl"
            )
        )


    def test_min_cycles(self):
        self.assertEqual(
            q.MIN_CYCLES,
            3
        )


    def test_full_pass_required(self):
        self.assertEqual(
            q.MIN_PASS_RATE,
            1.0
        )


    def test_no_rpc(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "c.rpc(",
            src
        )


    def test_no_private_key(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "QSB_SOLANA_PRIVATE_KEY",
            src
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

        self.assertNotIn(
            "c.send(",
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
