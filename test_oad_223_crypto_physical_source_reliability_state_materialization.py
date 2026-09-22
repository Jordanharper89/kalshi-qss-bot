import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_223_crypto_physical_source_reliability_state_materialization as m
class Cur:
    def __enter__(self): return self
    def __exit__(self,*x): return False
    def execute(self,*x): pass
    def fetchall(self): return [({"asset":"BTC"},),({"asset":"ETH"},)]
class Conn:
    def __enter__(self): return self
    def __exit__(self,*x): return False
    def cursor(self): return Cur()
    def rollback(self): pass
class T(unittest.TestCase):
    def test_hold(self):
        with patch.object(m,"connect",return_value=Conn()):
            r=m.materialize_physical_source_reliability_state()
        print("[STATE]",r.state)
        self.assertEqual(r.source_correctness_labels,0)
        self.assertIsNone(r.source_reliability_state_hash)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-223 truthful source-reliability materialization gate certified")
