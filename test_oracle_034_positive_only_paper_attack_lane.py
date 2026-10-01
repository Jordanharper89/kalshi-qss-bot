import inspect,unittest
from unittest.mock import patch
from qseries_v2.oracle_execution import oracle_034_positive_only_paper_attack_lane as q34

class T(unittest.TestCase):
    def test_safety(self):
        self.assertFalse(q34.EXECUTION_AUTHORITY)
        self.assertTrue(q34.PAPER_ONLY)

    def test_nonpositive_skipped(self):
        q34._ORIG_ATTEMPT=lambda *a,**k:(_ for _ in ()).throw(AssertionError("called"))
        w,rows=q34.positive_only_attempt("u",None,{
            "token":"T","start_lamports":1000,
            "pre_sim_net_lamports":0,"pre_sim_bps":0.0
        },"b")
        self.assertIsNone(w)
        self.assertEqual(rows[0]["status"],"NONPOSITIVE_NOT_ATTACKED")

    def test_positive_runs(self):
        q34._ORIG_ATTEMPT=lambda *a,**k:(None,[{"compiled":True}])
        w,rows=q34.positive_only_attempt("u",None,{
            "token":"T","start_lamports":1000,
            "pre_sim_net_lamports":10,"pre_sim_bps":100.0,
            "oracle034_compose_ms":2.0
        },"b")
        self.assertEqual(len(rows),1)

    def test_no_broadcast(self):
        self.assertNotIn("sendTransaction(",inspect.getsource(q34))

if __name__=="__main__":
    unittest.main(verbosity=2)
