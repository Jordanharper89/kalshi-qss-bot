import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_228_snapshot_market_behavior_maturity_materialization as m

ROWS=((1,"o","s","t",{"asset":"BTC","evidence_hash":"a"*64,"outcome_hash":"b"*64,"return_fraction":.01,"condition_vector":(("bitcoin","fee",1,"HIGH"),)}),
      (2,"p","s","t",{"asset":"BTC","evidence_hash":"c"*64,"outcome_hash":"d"*64,"return_fraction":-.02,"condition_vector":(("coinbase","spot",1,"OBSERVED"),)}))
class T(unittest.TestCase):
    def test_same_snapshot(self):
        snap=SimpleNamespace(as_of_sequence=2,snapshot_hash="f"*64,row_count=2,rows=ROWS)
        with patch.object(m,"capture_crypto_learned_case_snapshot",return_value=snap):
            a=m.materialize_snapshot_behavior_maturity()
            b=m.materialize_snapshot_behavior_maturity()
        print("[AS_OF]",a.as_of_sequence,"[MB]",a.market_behavior_state_hash,"[MAT]",a.maturity_state_hash)
        self.assertEqual(a.market_behavior_state_hash,b.market_behavior_state_hash)
        self.assertEqual(a.maturity_state_hash,b.maturity_state_hash)
        self.assertEqual(a.snapshot_hash,b.snapshot_hash)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-228 same-snapshot market behavior+maturity materialization certified")
