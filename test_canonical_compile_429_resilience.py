import ast
import unittest
from pathlib import Path

RUNTIME = Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")

class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = RUNTIME.read_text(encoding="utf-8")
        ast.parse(cls.src)

    def test_retry_helper_present(self):
        self.assertIn("def _canonical_compile_candidate_429_resilient(", self.src)

    def test_only_429_is_retried(self):
        self.assertIn('getattr(exc, "code", None) != 429', self.src)

    def test_bounded_retry(self):
        self.assertIn("for attempt in range(6):", self.src)
        self.assertIn("CANONICAL_COMPILE_RETRY_EXHAUSTED", self.src)

    def test_compile_current_uses_wrapper(self):
        start = self.src.index("def compile_current(")
        tail = self.src[start:]
        end_rel = tail.find("\ndef ", 20)
        block = tail if end_rel < 0 else tail[:end_rel]
        self.assertIn("_canonical_compile_candidate_429_resilient(", block)

    def test_no_execution_change(self):
        h0 = self.src.index("def _canonical_compile_candidate_429_resilient(")
        h1 = self.src.index("def compile_current(")
        self.assertNotIn("sendTransaction", self.src[h0:h1])

if __name__ == "__main__":
    unittest.main(verbosity=2)
