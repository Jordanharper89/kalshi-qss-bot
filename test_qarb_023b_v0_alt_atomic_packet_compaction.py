import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_023b_v0_alt_atomic_packet_compaction as q,
)


class FakeTx:
    def __init__(self, n):
        self.n = n

    def __bytes__(self):
        return b"x" * self.n


class T(unittest.TestCase):
    def test_known_1257_failure(self):
        r = q.choose_smallest([
            q.Candidate("PUMP_METEORA_ONLY", 1257, FakeTx(1257), 0)
        ])
        self.assertFalse(r.ok)
        self.assertEqual(r.status, "ATOMIC_TX_TOO_LARGE")
        self.assertEqual(r.over_by, 25)
        print("[PASS] known 1257-byte candidate fails closed by exactly 25 bytes")

    def test_compacted_packet_admitted(self):
        r = q.choose_smallest([
            q.Candidate("LEGACY", 1257, FakeTx(1257), 0),
            q.Candidate("V0_ALT_1", 1188, FakeTx(1188), 1),
        ])
        self.assertTrue(r.ok)
        self.assertEqual(r.best.label, "V0_ALT_1")
        self.assertEqual(r.best.size_bytes, 1188)
        print("[PASS] compact <=1232-byte packet admitted")

    def test_smallest_candidate_selected(self):
        r = q.choose_smallest([
            q.Candidate("A", 1210, FakeTx(1210), 1),
            q.Candidate("B", 1192, FakeTx(1192), 2),
        ])
        self.assertEqual(r.best.label, "B")
        print("[PASS] smallest candidate selected deterministically")

    def test_no_hot_io(self):
        src = inspect.getsource(q.compile_best_v0)
        for token in ("urlopen(", "requests.", "open(", "Path(", "sleep("):
            self.assertNotIn(token, src)
        print("[PASS] no REST/RPC/filesystem/sleep in compaction hot function")

    def test_execution_authority_false(self):
        self.assertIs(q.execution_authority, False)
        print("[PASS] execution_authority=FALSE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
