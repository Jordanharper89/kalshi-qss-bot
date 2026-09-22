import unittest
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_325_solana_universal_single_writer_persistence as m

class Obs:
    def __init__(self,oid): self.observation_id=oid

class T(unittest.TestCase):
    def setUp(self):
        self.orig={k:getattr(m,k) for k in (
            "build_universal_coverage_batch","_backend","_query_one",
            "submit_observation_batch","await_request","exact_postgresql_readback"
        )}

    def tearDown(self):
        for k,v in self.orig.items(): setattr(m,k,v)

    def _coverage(self):
        items=(Obs("a"),Obs("b"),Obs("c"))
        m.build_universal_coverage_batch=lambda *a,**k:SimpleNamespace(
            observations=items,transactions=7,state="UNIVERSAL_BATCH_ACCOUNTED"
        )
        m._backend=lambda root:object()
        return items

    def test_all_existing_is_idempotent_no_write(self):
        items=self._coverage()
        m._query_one=lambda backend,oid,i:SimpleNamespace(observation_id=oid)
        def forbidden(*a,**k): raise AssertionError("writer must not be called for existing observations")
        m.submit_observation_batch=forbidden
        m.await_request=forbidden
        m.exact_postgresql_readback=lambda ids,root:tuple(SimpleNamespace(observation_id=x) for x in ids)
        x=m.persist_solana_universal_chain_batch(100,1,".")
        self.assertEqual(x.observations,3)
        self.assertEqual(x.committed_events,3)
        self.assertIsNone(x.request_id)
        self.assertEqual(x.coverage_state,"UNIVERSAL_BATCH_ACCOUNTED")

    def test_mixed_replay_writes_only_missing_then_exact_readback(self):
        items=self._coverage()
        existing={"a","c"}
        m._query_one=lambda backend,oid,i:(SimpleNamespace(observation_id=oid) if oid in existing else None)
        captured=[]
        def submit(producer,priority,obs,root):
            captured.extend(x.observation_id for x in obs)
            return SimpleNamespace(request_id="req1")
        m.submit_observation_batch=submit
        m.await_request=lambda rid,root,timeout:(SimpleNamespace(accepted=True),)
        m.exact_postgresql_readback=lambda ids,root:tuple(SimpleNamespace(observation_id=x) for x in ids)
        x=m.persist_solana_universal_chain_batch(100,1,".")
        self.assertEqual(captured,["b"])
        self.assertEqual(x.request_id,"req1")
        self.assertEqual(x.committed_events,3)

    def test_commit_count_mismatch_fails_closed(self):
        self._coverage()
        m._query_one=lambda *a,**k:None
        m.submit_observation_batch=lambda *a,**k:SimpleNamespace(request_id="req2")
        m.await_request=lambda *a,**k:(SimpleNamespace(accepted=True),)
        m.exact_postgresql_readback=lambda *a,**k:()
        with self.assertRaises(RuntimeError):
            m.persist_solana_universal_chain_batch(100,1,".")

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-325 idempotent exact-readback foundational repair certified")
    print("[PASS] existing observations are not resubmitted")
    print("[PASS] mixed replay submits only missing observations")
    print("[PASS] exact PostgreSQL readback required before success")
