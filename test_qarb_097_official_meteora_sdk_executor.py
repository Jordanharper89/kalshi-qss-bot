from pathlib import Path
import inspect
import json
import re
import unittest

from qseries_v2.solana_live_execution import (
    qarb_097_official_meteora_sdk_executor
    as q
)


class T(unittest.TestCase):

    def test_q_series_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "Q_SERIES"
        )

        self.assertFalse(
            q.ORACLE_EXECUTION_AUTHORITY
        )


    def test_exact_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )

        self.assertAlmostEqual(
            q.MICRO_SOL,
            0.001
        )


    def test_official_meteora_helper(self):
        self.assertTrue(
            callable(
                q.native_meteora_swap_ixs
            )
        )


    def test_native_route_uses_official_builder(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            "native_meteora_swap_ixs",
            s
        )

        self.assertIn(
            "OFFICIAL_PUMP_TO_METEORA_SWAP2_FULL",
            s
        )


    def test_handcrafted_meteora_call_retired(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIsNone(
            re.search(
                r"\bdlmm_reverse_ix\s*\(",
                s
            )
        )


    def test_min_out_profitability(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            '"min_out"',
            s
        )

        self.assertIn(
            "guaranteed_net",
            s
        )


    def test_full_pump_helpers_preserved(self):
        s=inspect.getsource(
            q.native_live_route
        )

        self.assertIn(
            "p_ixs[:pi]",
            s
        )

        self.assertIn(
            "p_ixs[",
            s
        )


    def test_alt_reuse_preserved(self):
        self.assertTrue(
            callable(
                q._apply_saved_alt
            )
        )


    def test_signed_simulation_preserved(self):
        s=inspect.getsource(
            q.final_prepare
        )

        self.assertIn(
            "signed_simulation",
            s
        )


    def test_no_send_retry(self):
        import inspect

        src=inspect.getsource(
            q.send_once
        )

        self.assertIn(
            '"maxRetries":0',
            src
        )

        self.assertEqual(
            src.count(
                '"sendTransaction"'
            ),
            1
        )


    def test_node_meteora_builder_exists(self):
        p=Path(
            "qseries_v2/"
            "oracle_strategy_intelligence/"
            "solana_money/"
            "qsb059d_pump_native/"
            "build_meteora_swap_ix.mjs"
        )

        self.assertTrue(
            p.is_file()
        )

        s=p.read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "@meteora-ag/dlmm",
            s
        )

        self.assertIn(
            "pool.swap(",
            s
        )

        self.assertIn(
            "pool.swapQuote(",
            s
        )


    def test_sdk_version_pinned(self):
        p=Path(
            "qseries_v2/"
            "oracle_strategy_intelligence/"
            "solana_money/"
            "qsb059d_pump_native/"
            "package.json"
        )

        d=json.loads(
            p.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            d["dependencies"][
                "@meteora-ag/dlmm"
            ],
            "1.9.14"
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
