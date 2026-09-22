import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent.oad_399_solana_zero_cost_continuous_surveillance_worker import run_zero_cost_continuous_surveillance
class R:
    def __init__(self): self.admitted=True; self.wait_seconds=0; self.raw_type="dict"
class T(unittest.TestCase):
    def test_loop(self):
        with patch("qseries_v2.oracle_adapters.independent.oad_399_solana_zero_cost_continuous_surveillance_worker.run_governed_solana_worker_cycle",side_effect=[R(),R(),R()]):
            x=run_zero_cost_continuous_surveillance(max_cycles=3,sleep_fn=lambda s:None)
        print("[CONTINUOUS]",x)
        self.assertEqual(x.admitted_cycles,3)
        self.assertEqual(x.failures,0)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-399 zero-cost continuous surveillance worker certified")