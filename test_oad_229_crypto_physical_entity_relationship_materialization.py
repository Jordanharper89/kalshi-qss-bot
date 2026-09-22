import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_229_crypto_physical_entity_relationship_materialization as m
ROWS=((1,"o","s","t",{"asset":"BTC","evidence_hash":"a"*64,"outcome_hash":"b"*64,"return_fraction":.01,"condition_vector":(("bitcoin","fee",1,"HIGH"),("coinbase","spot",1,"OBSERVED"))}),)
class T(unittest.TestCase):
    def test_noncausal_relationship(self):
        snap=SimpleNamespace(as_of_sequence=1,rows=ROWS)
        with patch.object(m,"capture_crypto_learned_case_snapshot",return_value=snap):
            r=m.materialize_entity_relationship_state()
        print("[STATE]",r.state,"[REL]",len(r.relationships),"[HASH]",r.entity_relationship_state_hash)
        self.assertEqual(r.state,"MATERIALIZED_NON_CAUSAL_ASSOCIATIONS")
        self.assertEqual(len(r.entity_relationship_state_hash),64)
        self.assertTrue(all(x.relationship_type=="observed_condition_association" for x in r.relationships))

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-229 outcome-grounded non-causal entity relationship materialization certified")
