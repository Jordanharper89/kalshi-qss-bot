import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_008_physical_size_envelope_diagnostic as q
)


class T(unittest.TestCase):

    def test_paper_only(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


    def test_ladder(self):
        for x in (
            0.001,
            0.005,
            0.05,
            0.1,
            0.18,
            0.28,
            0.5,
            0.9,
            1.1,
            1.4,
        ):
            self.assertIn(
                x,
                q.SIZE_SOL
            )


    def test_parameterized_pump(self):
        s=inspect.getsource(
            q.physical_route_for_size
        )

        self.assertIn(
            "principal",
            s
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )


    def test_meteora(self):
        s=inspect.getsource(
            q.physical_route_for_size
        )

        self.assertIn(
            "q.meteora_swap",
            s
        )


    def test_packet_legality(self):
        s=inspect.getsource(
            q.inspect_packet
        )

        self.assertIn(
            "compile_signed",
            s
        )


    def test_no_broadcast(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "send_once(",
            s
        )

        self.assertNotIn(
            "sendTransaction",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
