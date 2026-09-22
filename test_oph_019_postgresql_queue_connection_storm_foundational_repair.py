import pickle
import unittest
from qseries_v2.oracle_production_hardening import oph_019_postgresql_universal_ingestion_queue as q
from qseries_v2.oracle_adapters.independent.oad_402_solana_zero_cost_surveillance_physical_gate import _is_transient_rpc_error

class T(unittest.TestCase):
    def test_await_reuses_one_connection(self):
        original=q.connect
        calls={"connect":0,"execute":0}
        class Cur:
            def __enter__(self): return self
            def __exit__(self,*a): return False
            def execute(self,*a,**k): calls["execute"]+=1
            def fetchone(self):
                if calls["execute"]<3:return ("PENDING",None,None,None)
                return ("DONE",pickle.dumps(("ok",),protocol=5),None,None)
        class Conn:
            def __enter__(self): return self
            def __exit__(self,*a): return False
            def cursor(self): return Cur()
        def fake_connect(*a,**k):
            calls["connect"]+=1
            return Conn()
        try:
            q.connect=fake_connect
            self.assertEqual(q.await_request("x",timeout_seconds=1,poll_seconds=.01),("ok",))
            self.assertEqual(calls["connect"],1)
            self.assertGreaterEqual(calls["execute"],3)
        finally:q.connect=original

    def test_timeout_classification(self):
        self.assertFalse(_is_transient_rpc_error(TimeoutError("PostgreSQL ingestion request timed out: abc")))
        self.assertTrue(_is_transient_rpc_error(TimeoutError("The read operation timed out")))

    def test_boundary(self):
        self.assertTrue(q.verify_oph_019_postgresql_universal_ingestion_queue())

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful():raise SystemExit(1)
    print("[PASS] OPH-019 foundational PostgreSQL connection-storm repair certified")
