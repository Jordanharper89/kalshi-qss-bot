import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_178_crypto_experience_evidence_lineage import build_crypto_experience_evidence_lineage,verify_crypto_experience_evidence_lineage
class T(unittest.TestCase):
    def test_lineage(self):
        c=SimpleNamespace(experience_id="e1",asset="BTC",evidence_hash="a"*64,condition_hash="b"*64,
            condition_vector=(("coinbase","spot_price",1.0,"OBSERVED"),("bitcoin","fastest_fee_rate",10.0,"ELEVATED")),
            temporal_vector=(("coinbase","spot_price","INCREASED",1.0,2.0,True),("bitcoin","fastest_fee_rate","UNCHANGED",0.0,0.0,True)))
        x=build_crypto_experience_evidence_lineage(c)
        print("[SOURCES]",x.source_families)
        print("[COMPARABLE]",x.comparable_metric_names)
        self.assertTrue(verify_crypto_experience_evidence_lineage(x))
        self.assertEqual(x.source_families,("bitcoin","coinbase"))
if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-178 crypto experience evidence lineage certified")
