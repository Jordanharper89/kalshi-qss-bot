import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_283_gmgn_continuous_runtime_checkpoint import *

class T(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            cp=advance_success(genesis_gmgn_runtime_checkpoint(),"TOKEN",("a","b","c"))
            save_gmgn_runtime_checkpoint(cp,d)
            q=load_gmgn_runtime_checkpoint(d)
            self.assertEqual(q.cycles,1); self.assertEqual(q.successes,1)
            self.assertEqual(q.last_token_address,"TOKEN")
            self.assertEqual(q.last_observation_ids,("a","b","c"))
            self.assertFalse(q.execution_authority)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-283 durable GMGN checkpoint certified")
