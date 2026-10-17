from pathlib import Path
import unittest

P=Path(
    "qseries_v2/oracle_execution/"
    "solana_atomic_executor/"
    "checkpoint2b_existing_alt_compaction.py"
)

class T(unittest.TestCase):

    def test_existing_alt_only(self):
        s=P.read_text(encoding="utf-8")

        self.assertIn(
            "recent_mriya_alt_keys",
            s
        )

        self.assertIn(
            "alt_sets",
            s
        )

        self.assertIn(
            "CHECKPOINT2B_FORWARD_ATOMIC_SIM_PASS",
            s
        )

    def test_no_broadcast(self):
        s=P.read_text(encoding="utf-8")

        self.assertNotIn(
            "sendTransaction(",
            s
        )

        self.assertNotIn(
            "bootstrap_micro_alt",
            s
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
