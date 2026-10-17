import ast
import unittest
from pathlib import Path

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "checkpoint3_reverse_atomic_compile.py"
)

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = TARGET.read_text(encoding="utf-8")
        ast.parse(cls.src)

    def test_reverse_builder_present(self):
        self.assertIn(
            "def _build_meteora_reverse_ix_hot(",
            self.src,
        )

    def test_reverse_route_uses_reverse_builder(self):
        start = self.src.index("def _reverse_route(")
        end = self.src.find("\ndef ", start + 20)
        if end < 0:
            end = len(self.src)
        block = self.src[start:end]
        self.assertIn(
            "_build_meteora_reverse_ix_hot(",
            block,
        )
        self.assertNotIn(
            "r.build_meteora_ix_hot(",
            block,
        )

    def test_direction_inverted(self):
        self.assertIn(
            "reverse_swap = not forward_swap",
            self.src,
        )

    def test_source_dest_swapped(self):
        self.assertIn(
            "accounts[4], accounts[5] = accounts[5], accounts[4]",
            self.src,
        )

    def test_zero_rpc_hot_builder(self):
        start = self.src.index(
            "def _build_meteora_reverse_ix_hot("
        )
        end = self.src.index("def _reverse_route(", start)
        block = self.src[start:end]
        self.assertNotIn(".rpc(", block)
        self.assertNotIn("getProgramAccounts", block)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction", self.src)

if __name__ == "__main__":
    unittest.main(verbosity=2)
