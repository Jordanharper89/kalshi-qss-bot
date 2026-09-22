import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_234_crypto_prospective_outcome_calibration_scoring as m

class Cur:
    def __init__(self):
        self.source=None
        self.sql=[]
    def __enter__(self):return self
    def __exit__(self,*x):return False
    def execute(self,s,args=None):
        self.sql.append(s)
        if args and isinstance(args,tuple) and args:
            self.source=args[0]
    def fetchall(self):
        return ()
class Conn:
    def __init__(self):self.c=Cur()
    def __enter__(self):return self
    def __exit__(self,*x):return False
    def cursor(self):return self.c
    def rollback(self):pass

class T(unittest.TestCase):
    def test_source_indexed_bounded_reads(self):
        c=Conn()
        with patch.object(m,"connect",return_value=c):
            rows=m.read_and_score_mature_prospective_cases(per_source_limit=32)
        self.assertEqual(rows,())
        reads=[x for x in c.c.sql if "FROM public.oracle_canonical_observations" in x]
        print("[READS]",len(reads))
        self.assertEqual(len(reads),6)
        self.assertTrue(all("WHERE source_id=%s" in x for x in reads))
        self.assertTrue(all("ORDER BY sequence_number DESC" in x for x in reads))
        self.assertTrue(all("observation_type=" not in x.split("WHERE",1)[1].split("ORDER BY",1)[0] for x in reads))
        self.assertFalse(any("ORDER BY sequence_number ASC" in x for x in reads))

    def test_brier_contract(self):
        o=m.build_outcome_observation("BTC","prospective_positive_return_60s",1,"t","prospective:x","a"*64)
        e=m.assemble_learning_event("BTC","b"*64,"c"*64,o)
        x=m.learn_calibration(e,.7,True)
        delta=.25-x.brier_score
        print("[BRIER]",x.brier_score,"[DELTA]",delta)
        self.assertAlmostEqual(x.brier_score,.09)
        self.assertGreater(delta,0)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-234 source-indexed prospective scoring contract certified")
