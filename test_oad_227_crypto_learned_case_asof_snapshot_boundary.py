import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent import oad_227_crypto_learned_case_asof_snapshot_boundary as m

class Cur:
    def __init__(self):self.n=0;self.sql=[]
    def __enter__(self):return self
    def __exit__(self,*x):return False
    def execute(self,s,args=None):self.sql.append(s)
    def fetchone(self):return (100,)
    def fetchall(self):
        self.n+=1
        return [(97+self.n,f"o{self.n}",m.SOURCE_IDS[(self.n-1)%3],"t",{"asset":"BTC"})]
class Conn:
    def __init__(self):self.c=Cur()
    def __enter__(self):return self
    def __exit__(self,*x):return False
    def cursor(self):return self.c
    def rollback(self):pass

class T(unittest.TestCase):
    def test_snapshot(self):
        c=Conn()
        with patch.object(m,"connect",return_value=c):
            a=m.capture_crypto_learned_case_snapshot()
        print("[AS_OF]",a.as_of_sequence,"[ROWS]",a.row_count,"[HASH]",a.snapshot_hash)
        self.assertEqual(a.as_of_sequence,100)
        self.assertEqual(a.row_count,3)
        self.assertEqual(len(a.snapshot_hash),64)
        self.assertTrue(any("sequence_number<=%s" in x for x in c.c.sql))
        self.assertTrue(any("REPEATABLE READ READ ONLY" in x for x in c.c.sql))
        self.assertFalse(a.probability_enabled)

if __name__=="__main__":
    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not x.wasSuccessful():raise SystemExit(1)
    print("[PASS] OAD-227 stable as-of learned-case snapshot boundary certified")
