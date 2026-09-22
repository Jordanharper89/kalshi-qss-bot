import unittest
from unittest.mock import patch
from datetime import datetime,timezone
from qseries_v2.oracle_adapters.independent import oad_224_crypto_physical_market_behavior_state_materialization as m
ROWS=[(datetime.now(timezone.utc),{"asset":"BTC","evidence_hash":"a"*64,"outcome_hash":"b"*64,"return_fraction":.01}),
(datetime.now(timezone.utc),{"asset":"BTC","evidence_hash":"c"*64,"outcome_hash":"d"*64,"return_fraction":-.02}),
(datetime.now(timezone.utc),{"asset":"ETH","evidence_hash":"e"*64,"outcome_hash":"f"*64,"return_fraction":.03})]
class Cur:
    def __enter__(self):return self
    def __exit__(self,*x):return False
    def execute(self,*x):pass
    def fetchall(self):return ROWS
class Conn:
    def __enter__(self):return self
    def __exit__(self,*x):return False
    def cursor(self):return Cur()
    def rollback(self):pass
class T(unittest.TestCase):
    def test_materialize(self):
        with patch.object(m,"connect",return_value=Conn()):
            r=m.materialize_physical_market_behavior_state()
        print("[STATE]",r.state,"[OBS]",r.behavior_observations,"[HASH]",r.market_behavior_state_hash)
        self.assertEqual(r.state,"MATERIALIZED");self.assertEqual(len(r.market_behavior_state_hash),64);self.assertEqual(len(r.behavior_states),2)
if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-224 outcome-grounded market behavior materialization certified")
