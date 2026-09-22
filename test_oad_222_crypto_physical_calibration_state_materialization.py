import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_222_crypto_physical_calibration_state_materialization as m
class Cur:
    def __enter__(self): return self
    def __exit__(self,*x): return False
    def execute(self,*x): pass
    def fetchall(self): return [({"asset":"BTC","probability":None},),({"asset":"ETH","probability":None},)]
class Conn:
    def __enter__(self): return self
    def __exit__(self,*x): return False
    def cursor(self): return Cur()
    def rollback(self): pass
class T(unittest.TestCase):
    def test_hold_without_forecasts(self):
        with patch.object(m,"connect",return_value=Conn()):
            r=m.materialize_physical_calibration_state()
        print("[STATE]",r.state)
        self.assertEqual(r.cases_with_historical_forecast_probability,0)
        self.assertIsNone(r.calibration_state_hash)
        self.assertFalse(r.probability_enabled)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-222 truthful physical calibration materialization gate certified")
