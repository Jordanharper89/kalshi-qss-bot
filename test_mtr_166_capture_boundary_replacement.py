
import tempfile
import unittest
from unittest.mock import Mock

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_166_capture_boundary_replacement as m
)


class Tests(unittest.TestCase):

    def test_all_counters_initialized(self):
        counters = m.new_counters()

        self.assertEqual(len(counters), 6)

        for value in counters.values():
            self.assertEqual(value, 0)

    def test_empty_counter_dictionary(self):
        counters = {}
        lane = Mock()
        lane.newer_waiting.return_value = False

        cb = m.capture_callback("public", "unused", counters)

        cb(
            lane,
            "token",
            {},
            {"direction": "METEORA_TO_PUMP", "start": 10000000},
            1,
            1,
            1,
        )

        self.assertEqual(counters["positive_seen"], 1)
        self.assertEqual(counters["wrong_direction"], 1)

    def test_same_dictionary_is_updated(self):
        counters = m.new_counters()
        lane = Mock()
        lane.newer_waiting.return_value = False

        cb = m.capture_callback("public", "unused", counters)

        cb(
            lane,
            "token",
            {},
            {"direction": "METEORA_TO_PUMP", "start": 10000000},
            1,
            1,
            1,
        )

        self.assertEqual(counters["wrong_direction"], 1)

    def test_superseded_rejected(self):
        counters = {}
        lane = Mock()
        lane.newer_waiting.return_value = True

        cb = m.capture_callback("public", "unused", counters)

        cb(
            lane,
            "token",
            {},
            {"direction": "PUMP_TO_METEORA", "start": 10000000},
            1,
            1,
            1,
        )

        self.assertEqual(counters["superseded"], 1)
        self.assertEqual(counters["captured"], 0)

    def test_wrong_size_rejected(self):
        counters = {}
        lane = Mock()
        lane.newer_waiting.return_value = False

        cb = m.capture_callback("public", "unused", counters)

        cb(
            lane,
            "token",
            {},
            {"direction": "PUMP_TO_METEORA", "start": 5000000},
            1,
            1,
            1,
        )

        self.assertEqual(counters["wrong_size"], 1)
        self.assertEqual(counters["captured"], 0)

    def test_no_execution_authority(self):
        import inspect

        source = inspect.getsource(m.capture_callback)

        forbidden = (
            "signed_tx(",
            "keypair(",
            "send_transaction(",
            "simulate_current(",
            "compile_current(",
        )

        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
