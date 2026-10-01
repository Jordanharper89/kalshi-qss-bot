import base64
import inspect
import struct
import unittest

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

    def test_meteora_hot_builder_zero_rpc(self):

        src=inspect.getsource(
            q.build_meteora_ix_hot
        )

        forbidden=[
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
            "http(",
        ]

        for text in forbidden:
            self.assertNotIn(
                text,
                src,
            )

    def test_same_snapshot_route_no_old_dlmm_builder(self):

        src=inspect.getsource(
            q.same_snapshot_route
        )

        self.assertNotIn(
            "dlmm_reverse_ix(",
            src,
        )

        self.assertIn(
            "build_meteora_ix_hot(",
            src,
        )

    def test_meteora_hot_instruction_shape(self):

        q.METEORA_TEMPLATES={
            "TOKEN":{
                "pool":"POOL",
                "token_x":"TOKEN",
                "token_y":q.q87.c.WSOL,
                "swap_for_y":True,
                "arrays":[
                    (1,"ARRAY1"),
                    (2,"ARRAY2"),
                    (3,"ARRAY3"),
                ],
                "fixed_accounts":[
                    (
                        "POOL",
                        False,
                        True,
                    ),
                ],
            }
        }

        quote={
            "swap_for_y":True,
            "raw_out":
                1_234_567,
            "bins_crossed":
                71,
        }

        ix=q.build_meteora_ix_hot(
            "TOKEN",
            555,
            quote,
        )

        self.assertEqual(
            ix["programId"],
            q.q87.c.DLMM,
        )

        raw=base64.b64decode(
            ix["data"]
        )

        self.assertEqual(
            raw[:8],
            bytes([
                248,
                198,
                158,
                145,
                225,
                117,
                135,
                200,
            ]),
        )

        amount_in,min_out=(
            struct.unpack(
                "<QQ",
                raw[8:24],
            )
        )

        self.assertEqual(
            amount_in,
            555,
        )

        self.assertEqual(
            min_out,
            1_234_567
            *(
                10000
                -q.q87.las.q59.SLIPPAGE_BPS
            )
            //10000,
        )

        #
        # crossed=71 => 2 arrays.
        #
        array_accounts=[
            x["pubkey"]
            for x in ix[
                "accounts"
            ]
            if x["pubkey"].startswith(
                "ARRAY"
            )
        ]

        self.assertEqual(
            array_accounts,
            [
                "ARRAY1",
                "ARRAY2",
            ],
        )

    def test_exact_quote_semantics_preserved(self):

        src=inspect.getsource(
            q.rewrite_pump_buy_bounds
        )

        self.assertIn(
            "BUY_EXACT_QUOTE_IN_DISC",
            src,
        )

    def test_truth_sim_decoder_preserved(self):

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

        self.assertNotIn(
            "q87.c.simulate(",
            src,
        )

    def test_no_old_runtime_chain(self):

        src=inspect.getsource(
            q
        )

        self.assertNotIn(
            "q20.run(",
            src,
        )

        self.assertNotIn(
            "persistent.serve(",
            src,
        )

        self.assertNotIn(
            "SimulationLane(",
            src,
        )

    def test_no_broadcast(self):

        src=inspect.getsource(
            q
        )

        self.assertNotIn(
            "sendTransaction",
            src,
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
