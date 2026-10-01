import inspect
import unittest
from unittest.mock import patch

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as q
)


class T(unittest.TestCase):

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

    def test_6040_left_parser(self):

        sim={
            "err":{
                "InstructionError":[
                    3,
                    {
                        "Custom":6040
                    },
                ]
            },
            "logs":[
                "Program log: AnchorError Error Code: BuySlippageBelowMinBaseAmountOut",
                "Program log: Left: 14030784113",
                "Program log: Right: 14927620303",
            ],
        }

        self.assertEqual(
            q.pump_6040_actual_base_out(
                sim
            ),
            14030784113,
        )

    def test_non_6040_not_recovered(self):

        sim={
            "err":{
                "InstructionError":[
                    3,
                    {
                        "Custom":6004
                    },
                ]
            },
            "logs":[
                "Program log: Left: 123"
            ],
        }

        self.assertIsNone(
            q.pump_6040_actual_base_out(
                sim
            )
        )

    def test_chain_reprice_uses_token_net_and_dlmm(self):

        opportunity={
            "start":1000,
            "size_sol":.000001,
            "local_bps":100.0,
            "local_net":10,
            "pump_base_out_gross":2000,
            "pump_base_out_net":1900,
            "pump_max_quote":1000,
            "mq":{
                "raw_out":1010
            },
        }

        snap={
            "token":"TOKEN",
            "meteora":{},
            "dlmm_state":object(),
        }

        with patch.object(
            q.q18,
            "token_net",
            return_value=1800,
        ):
            with patch.object(
                q.q18.core,
                "dlmm_quote_snapshot",
                return_value={
                    "raw_out":1050,
                    "bins_crossed":1,
                    "swap_for_y":True,
                    "arrays":[],
                },
            ):
                x=q.reprice_from_pump_chain_truth(
                    snap,
                    opportunity,
                    1900,
                )

        self.assertEqual(
            x["pump_base_out_gross"],
            1900,
        )

        self.assertEqual(
            x["pump_base_out_net"],
            1800,
        )

        self.assertEqual(
            x["local_end"],
            1050,
        )

        self.assertEqual(
            x["local_net"],
            50,
        )

        self.assertTrue(
            x["pump_chain_truth"]
        )

    def test_attack_has_one_6040_retry(self):

        src=inspect.getsource(
            q.attack
        )

        self.assertIn(
            "pump_6040_actual_base_out",
            src,
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src,
        )

        self.assertIn(
            "[SAE002_PUMP_CHAIN_TRUTH]",
            src,
        )

        self.assertIn(
            "[SAE002_CHAIN_REPRICE_HOLD]",
            src,
        )

        self.assertIn(
            "[SAE002_REPRICE_SIM_REJECT]",
            src,
        )

    def test_hot_meteora_builder_stays_rpc_free(self):

        src=inspect.getsource(
            q.build_meteora_ix_hot
        )

        for bad in (
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
            "http(",
        ):
            self.assertNotIn(
                bad,
                src,
            )

    def test_exact_quote_instruction_preserved(self):

        src=inspect.getsource(
            q.rewrite_pump_buy_bounds
        )

        self.assertIn(
            "BUY_EXACT_QUOTE_IN_DISC",
            src,
        )

    def test_truth_sim_preserved(self):

        src=inspect.getsource(
            q.simulate_current
        )

        self.assertIn(
            '"simulateTransaction"',
            src,
        )

        self.assertIn(
            'result.get(\n        "value"',
            src,
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
