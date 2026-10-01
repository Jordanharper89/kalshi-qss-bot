import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_090_current_executable_liquidity_intake_gate as q


class T(unittest.TestCase):

    def test_positive_remembered_admitted(self):
        row={
            "selected_binding":{
                "net_lamports":100,
                "net_bps":25.0,
                "recovered_from_remembered":False,
            }
        }

        self.assertTrue(
            q.physical_row_ok(
                row
            )
        )


    def test_negative_rejected(self):
        row={
            "selected_binding":{
                "net_lamports":-1,
                "net_bps":-1.0,
                "recovered_from_remembered":False,
            }
        }

        self.assertFalse(
            q.physical_row_ok(
                row
            )
        )


    def test_incomplete_rejected(self):
        self.assertFalse(
            q.physical_row_ok({
                "status":
                    "NO_CURRENT_COMPLETE_DLMM_LIQUIDITY"
            })
        )


    def test_alternate_not_silently_cutover(self):
        row={
            "selected_binding":{
                "net_lamports":100,
                "net_bps":50,
                "recovered_from_remembered":True,
            }
        }

        self.assertFalse(
            q.physical_row_ok(
                row
            )
        )


    def test_selection_preserves_original_binding(self):
        memory=[{
            "token":"T",
            "pump_pool":"P",
            "meteora_meta":{
                "address":"M"
            },
            "size_sol":1.4,
        }]

        report={
            "results":{
                "T":{
                    "selected_binding":{
                        "size_sol":0.5,
                        "meteora_pool":"M",
                        "net_lamports":10,
                        "net_bps":20,
                        "recovered_from_remembered":False,
                    }
                }
            }
        }

        selected,rejected=(
            q.select_bindings(
                memory,
                report
            )
        )

        self.assertEqual(
            len(selected),
            1
        )

        self.assertEqual(
            selected[0][
                "meteora_meta"
            ][
                "address"
            ],
            "M"
        )

        self.assertEqual(
            rejected,
            []
        )


    def test_ranked_best_bps_first(self):
        memory=[
            {
                "token":"A",
                "pump_pool":"PA",
                "meteora_meta":{
                    "address":"MA"
                },
                "size_sol":1,
            },
            {
                "token":"B",
                "pump_pool":"PB",
                "meteora_meta":{
                    "address":"MB"
                },
                "size_sol":1,
            },
        ]

        report={
            "results":{
                "A":{
                    "selected_binding":{
                        "size_sol":1,
                        "meteora_pool":"MA",
                        "net_lamports":1,
                        "net_bps":10,
                        "recovered_from_remembered":False,
                    }
                },
                "B":{
                    "selected_binding":{
                        "size_sol":1,
                        "meteora_pool":"MB",
                        "net_lamports":2,
                        "net_bps":20,
                        "recovered_from_remembered":False,
                    }
                },
            }
        }

        selected,_=q.select_bindings(
            memory,
            report
        )

        self.assertEqual(
            selected[0]["token"],
            "B"
        )


    def test_exact_memory_source(self):
        self.assertTrue(
            callable(
                q.q86.memory_candidates
            )
        )


    def test_exact_089_state(self):
        self.assertTrue(
            str(
                q.q89.STATE
            ).endswith(
                "qarb_089_two_second_dlmm_liquidity_binding_recovery.json"
            )
        )


    def test_no_memory_mutation(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "qarb_080_binding_memory.json",
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
