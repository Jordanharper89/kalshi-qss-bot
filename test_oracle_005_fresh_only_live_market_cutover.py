import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as q
)


class T(unittest.TestCase):

    def test_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )


    def test_exact_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_fresh_only(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            "hot_seconds",
            s
        )

        self.assertIn(
            "seconds_since_last_seen",
            s
        )

        self.assertIn(
            "age>hot_seconds",
            s
        )


    def test_no_execution_memory_fallback(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertNotIn(
            "q80.select_rows",
            s
        )

        self.assertNotIn(
            "q80.MEMORY",
            s
        )


    def test_live_mriya_discovery(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            "run_qarb_043b_paced_mriya_token_discovery.py",
            s
        )

        self.assertIn(
            "q80.q45.classify",
            s
        )


    def test_current_binding_required(self):
        s=inspect.getsource(
            q.live_universe_rows
        )

        self.assertIn(
            'meta.get(',
            s
        )

        self.assertIn(
            '"pump_pool"',
            s
        )


    def test_strategy_unchanged(self):
        s=inspect.getsource(
            q.exact_route
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )

        self.assertIn(
            "meteora_swap",
            s
        )


    def test_signed_physical_gate(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
