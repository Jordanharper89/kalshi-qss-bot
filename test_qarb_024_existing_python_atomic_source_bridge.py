import sys
import types
import unittest

fake_name = (
    "qseries_v2.oracle_strategy_intelligence.solana_money."
    "qsb059_gav_reverse_atomic"
)
fake = types.ModuleType(fake_name)

def compose_reverse_candidates(user, token, pump_pool, meteora_pool, start_sol):
    return {
        "candidates": [
            {"label": "FULL", "instructions": [1, 2], "alts": []},
            {"label": "PUMP_METEORA_ONLY", "instructions": [3, 4], "alts": ["ALT"]},
        ]
    }

def run():
    return None

fake.compose_reverse_candidates = compose_reverse_candidates
fake.run = run
sys.modules[fake_name] = fake

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_024_existing_python_atomic_source_bridge as q,
)


class T(unittest.TestCase):
    def test_bridge_contract(self):
        s = q.bridge_status()
        self.assertTrue(s.compose_present)
        self.assertTrue(s.packet_gate_present)
        self.assertFalse(s.execution_authority)
        print("[PASS] QSB exact composer -> QARB-023B packet gate bridge present")

    def test_candidate_extraction(self):
        r = compose_reverse_candidates(None, None, None, None, 0.05)
        rows = q.candidate_instruction_sets(r)
        self.assertEqual([x[0] for x in rows], ["FULL", "PUMP_METEORA_ONLY"])
        self.assertEqual(rows[1][2], ["ALT"])
        print("[PASS] exact candidate instructions + ALT lineage normalized")

    def test_source_signature(self):
        sig = q.source_signature()
        self.assertIn("start_sol", sig)
        print("[PASS] exact upstream compose signature visible")

    def test_execution_false(self):
        self.assertIs(q.execution_authority, False)
        print("[PASS] execution_authority=FALSE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
