import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mry_003_hot_rotation as m
class T(unittest.TestCase):
    def test_budget(self):
        inv=[{"index":i,"token":str(i),"account_cost":100,"source":"WARM"} for i in range(10)]
        s=m.select_hot(inv,target=20,account_budget=480)
        self.assertEqual(len(s),4)
    def test_view(self):
        st={"pairs":[1,2],"preg":{"a":(0,"X"),"b":(1,"Y")},"addresses":["a","b"]}
        v=m.hot_view(st,[{"index":1,"token":"T"}])
        self.assertEqual(v["addresses"],["b"])
if __name__=="__main__":unittest.main(verbosity=2)
