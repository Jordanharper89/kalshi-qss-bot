import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as m
class T(unittest.TestCase):
    def test_config(self):
        self.assertGreaterEqual(m.configure(40),40)
        self.assertGreaterEqual(m.engine.MAX_TOKENS,40)
        self.assertGreaterEqual(m.engine.DISCOVERY_BUDGET,96)
    def test_worker_contract(self):
        w=m.ReplenishmentWorker(".",20)
        self.assertEqual(w.generation,0)
        g,rows=w.latest()
        self.assertEqual(g,0);self.assertEqual(rows,[])
if __name__=="__main__":unittest.main(verbosity=2)
