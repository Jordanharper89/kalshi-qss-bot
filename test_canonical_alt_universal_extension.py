import unittest
from pathlib import Path

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "canonical_alt_universal_extension.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = TARGET.read_text(encoding="utf-8")

    def test_existing_table_only(self):
        self.assertIn(
            "HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r",
            self.s,
        )
        self.assertNotIn("CreateLookupTable", self.s)

    def test_exact_nine_shared(self):
        rows = (
            "8axdqvEoZ5YkV1yGw5Cmsx9pkeVve4cM9wAkZfhPcRDp",
            "Hvb4rCzCrUHxijoopBfN8q4SRmVeeKfPSEKKWGKMAfHZ",
            "5PHirr8joyTMp9JMm6nW7hNDVyEYdkzDqazxPD7RaTjx",
            "C2aFPdENg4A2HQsmrd5rTw5TaYBX5Ku887cWjbFKtZpw",
            "D1ZN9Wj1fRSUQfCjhvnu1hqDMT7hzjzBBpi12nVniYD6",
            "GS4CU59F31iL7aR2Q8zVS8DRrcRnXX1yjQ66TqNVQnaR",
            "pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ",
            "GAFuhgcd328SkkBYHpfadzmef9hTGAFRCi9QoCnsZQug",
            "9M4giFFMxmFGXtc3feFzRai56WbBqehoSeRE5GK7gf7",
        )
        for row in rows:
            self.assertIn(row, self.s)

    def test_guarded_broadcast(self):
        self.assertIn("ORACLE_CANONICAL_ALT_EXTEND", self.s)
        self.assertIn("EXTEND_CANONICAL_ALT_UNIVERSAL", self.s)
        self.assertIn("args.extend", self.s)

    def test_simulation_before_send(self):
        self.assertLess(
            self.s.index("[CANONICAL_ALT_EXTEND_SIM_PASS]"),
            self.s.index("signature = c.send(raw)"),
        )

    def test_onchain_verify(self):
        self.assertIn("verified_all_shared_present", self.s)
        self.assertIn("still_missing", self.s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
