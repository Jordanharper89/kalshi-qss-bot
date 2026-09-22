import unittest
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_325_solana_universal_single_writer_persistence as m

class Obs:
    def __init__(self,oid): self.observation_id=oid

class FakeCursor:
    def __init__(self,existing): self.existing=existing; self.rows=[]; self.select_calls=0
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def execute(self,sql,args=None):
        if sql.startswith("SET LOCAL"): return
        if "WHERE observation_id = ANY" in sql:
            self.select_calls+=1
            ids=args[0]; self.rows=[(x,) for x in ids if x in self.existing]; return
        raise AssertionError(sql)
    def fetchall(self): return list(self.rows)

class FakeConn:
    def __init__(self,existing,cursors): self.existing=existing; self.cursors=cursors
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def cursor(self):
        c=FakeCursor(self.existing); self.cursors.append(c); return c

class T(unittest.TestCase):
    def setUp(self):
        self.orig={k:getattr(m,k) for k in ("build_universal_coverage_batch","connect","submit_observation_batch","await_request")}
    def tearDown(self):
        for k,v in self.orig.items(): setattr(m,k,v)
    def test_bulk_reader_uses_one_connection_and_chunked_queries(self):
        cursors=[]; existing={"0","500","1000","1499"}
        m.connect=lambda *a,**k:FakeConn(existing,cursors)
        found=m._bulk_existing_observation_ids(tuple(str(i) for i in range(1500)),".",chunk_size=1000)
        self.assertEqual(found,existing); self.assertEqual(len(cursors),1); self.assertEqual(cursors[0].select_calls,2)
    def test_all_existing_skips_writer_and_bulk_verifies(self):
        items=tuple(Obs(x) for x in ("a","b","c")); existing={"a","b","c"}; cursors=[]
        m.build_universal_coverage_batch=lambda *a,**k:SimpleNamespace(observations=items,transactions=3,state="UNIVERSAL_BATCH_ACCOUNTED")
        m.connect=lambda *a,**k:FakeConn(existing,cursors)
        m.submit_observation_batch=lambda *a,**k:(_ for _ in ()).throw(AssertionError("writer should not run"))
        m.await_request=lambda *a,**k:()
        x=m.persist_solana_universal_chain_batch(100,1,".")
        self.assertEqual(x.committed_events,3); self.assertIsNone(x.request_id); self.assertEqual(len(cursors),2)
    def test_mixed_replay_submits_only_missing_then_bulk_readback(self):
        items=tuple(Obs(x) for x in ("a","b","c")); existing={"a","c"}; cursors=[]; submitted=[]
        m.build_universal_coverage_batch=lambda *a,**k:SimpleNamespace(observations=items,transactions=3,state="UNIVERSAL_BATCH_ACCOUNTED")
        m.connect=lambda *a,**k:FakeConn(existing,cursors)
        def submit(prod,pri,obs,root):
            submitted.extend(x.observation_id for x in obs); existing.update(submitted); return SimpleNamespace(request_id="r1")
        m.submit_observation_batch=submit
        m.await_request=lambda *a,**k:(SimpleNamespace(accepted=True),)
        x=m.persist_solana_universal_chain_batch(100,1,".")
        self.assertEqual(submitted,["b"]); self.assertEqual(x.committed_events,3); self.assertEqual(x.request_id,"r1")

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-325 bulk idempotent readback foundational repair certified")
    print("[PASS] no per-observation PostgreSQL N+1 read path")
    print("[PASS] bounded bulk pre-read and exact bulk post-readback")
