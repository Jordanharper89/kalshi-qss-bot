import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_225_crypto_physical_maturity_state_materialization as m
class Cur:
    def __enter__(self):return self
    def __exit__(self,*x):return False
    def execute(self,*x):pass
    def fetchall(self):return [({"return_fraction":.01,"condition_vector":(("bitcoin","fee",1,"HIGH"),)},),({"return_fraction":-.02,"condition_vector":(("coinbase","spot",1,"OBSERVED"),)},),({"return_fraction":.03,"condition_vector":(("ethereum","fee",1,"HIGH"),)},)]
class Conn:
    def __enter__(self):return self
    def __exit__(self,*x):return False
    def cursor(self):return Cur()
    def rollback(self):pass
class T(unittest.TestCase):
    def test_uncalibrated(self):
        with patch.object(m,"connect",return_value=Conn()):
            r=m.materialize_physical_maturity_state()
        print("[BAND]",r.maturity.maturity_band,"[SCORE]",r.maturity.maturity_score,"[HASH]",r.maturity_state_hash)
        self.assertEqual(r.calibration_quality,0.0);self.assertEqual(r.maturity.maturity_score,0.0);self.assertEqual(r.maturity.maturity_band,"immature");self.assertEqual(len(r.maturity_state_hash),64)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-225 uncalibrated maturity state materialization certified")
