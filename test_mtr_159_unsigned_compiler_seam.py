
import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_159_unsigned_compiler_seam as m
class Tests(unittest.TestCase):
    def test_compile_current_is_real(self):
        self.assertTrue(any(x["function"] == "compile_current"
                            for x in m.definitions(m.RUNTIME, {"compile_current"})))
    def test_import_is_traceable(self):
        self.assertTrue(m.trace_import(), "q87 import must be resolved, not guessed")
    def test_no_execution(self):
        r = m.inspect()
        self.assertFalse(r["compiler_invoked"])
        self.assertFalse(r["private_key_used"])
        self.assertFalse(r["signing"])
        self.assertFalse(r["broadcast"])
        self.assertFalse(r["unsigned_path_certified"])
if __name__ == "__main__":
    unittest.main(verbosity=2)
