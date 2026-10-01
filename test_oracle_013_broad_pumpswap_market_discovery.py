import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as e
)

from qseries_v2.oracle_execution import (
    oracle_013_pumpswap_program_discovery
    as d
)


class T(unittest.TestCase):

    def test_discovery_read_only(self):

        self.assertFalse(
            d.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            d.READ_ONLY
        )


    def test_pump_program_source(self):

        self.assertEqual(
            d.PUMP,
            e.base.q87.c.PUMP
        )


    def test_separate_registry(self):

        self.assertIn(
            "oracle_013_pumpswap_program_tokens.json",
            str(
                d.STATE
            )
        )


    def test_mriya_preserved(self):

        s=inspect.getsource(
            e._ensure_oracle_discovery
        )

        self.assertIn(
            "run_qarb_043b_paced_mriya_token_discovery.py",
            s
        )


    def test_broad_discovery_added(self):

        s=inspect.getsource(
            e._ensure_broad_discovery
        )

        self.assertIn(
            "run_oracle_013_pumpswap_program_discovery.py",
            s
        )


    def test_registry_merge(self):

        s=inspect.getsource(
            e._merged_discovery_registry
        )

        self.assertIn(
            "MRIYA",
            s
        )

        self.assertIn(
            "PUMPSWAP_PROGRAM",
            s
        )


    def test_exact_binding_still_required(self):

        s=inspect.getsource(
            e.refresh_live_universe_rows
        )

        self.assertIn(
            "_classify_merged_discovery",
            s
        )

        self.assertIn(
            "pump_pool",
            s
        )

        self.assertIn(
            "meteora_meta",
            s
        )


    def test_no_stale_memory_fallback(self):

        s=inspect.getsource(
            e.refresh_live_universe_rows
        )

        self.assertNotIn(
            "q80.select_rows",
            s
        )

        self.assertNotIn(
            "q80.MEMORY",
            s
        )


    def test_discovery_has_no_execution(self):

        with open(
            d.__file__,
            encoding="utf-8"
        ) as f:
            s=f.read()

        self.assertNotIn(
            "sendTransaction",
            s
        )

        self.assertNotIn(
            "send_once(",
            s
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
