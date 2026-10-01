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


    def test_micro_cap(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_exact_pump_minimum_parsed(self):
        s=inspect.getsource(
            q.pump_min_base_out
        )

        self.assertIn(
            "raw[16:24]",
            s
        )


    def test_token2022_net_used(self):
        s=inspect.getsource(
            q.exact_route
        )

        self.assertIn(
            "net_received",
            s
        )

        self.assertIn(
            "pump_minimum",
            s
        )


    def test_same_packet_boundary(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            'base.send_once(',
            s
        )

        self.assertIn(
            'top["raw"]',
            s
        )


    def test_signed_simulation_before_pass(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


    def test_rpc_backoff(self):
        s=inspect.getsource(
            q.rpc
        )

        self.assertIn(
            "429",
            s
        )


    def test_no_alt_creation(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "createLookupTable",
            s
        )

        self.assertNotIn(
            "bootstrap_micro_alt",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
