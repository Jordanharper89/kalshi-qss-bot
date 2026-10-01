import unittest
from unittest.mock import patch

from qseries_v2.oracle_execution import (
    oracle_039_direct_rpc_wealth_accounting_replacement as q39
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(
            q39.EXECUTION_AUTHORITY
        )
        self.assertTrue(
            q39.PAPER_ONLY
        )
        self.assertFalse(
            q39.REAL_MONEY_MOVED
        )

    def test_direct_rpc_result(self):
        with patch.object(
            q39.c,
            "http",
            return_value={
                "jsonrpc":"2.0",
                "id":1,
                "result":{"value":123},
            },
        ):
            x=q39.rpc_direct(
                "getBalance",
                [],
            )

        self.assertEqual(
            x["value"],
            123,
        )

    def test_sim_nested_value(self):
        with patch.object(
            q39,
            "rpc_direct",
            return_value={
                "context":{"slot":1},
                "value":{
                    "err":None,
                    "accounts":[
                        {"lamports":100},
                        None,
                        None,
                    ],
                    "unitsConsumed":77,
                },
            },
        ):
            v=q39.simulation_value(
                b"x",
                ["U","W","T"],
                False,
            )

        self.assertIsNone(
            v["err"]
        )
        self.assertEqual(
            v["unitsConsumed"],
            77,
        )

    def test_bool_result_rejected_cleanly(self):
        with patch.object(
            q39,
            "rpc_direct",
            return_value=True,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "BALANCE_RESULT_NOT_MAPPING",
            ):
                q39.native_balance("U")

    def test_install_replaces_q88_wealth(self):
        q39.install()

        self.assertIs(
            q39.q38.q88.simulate_wealth,
            q39.simulate_wealth,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
