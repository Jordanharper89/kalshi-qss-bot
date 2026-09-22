import unittest
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_326_solana_universal_resilient_worker as m

class T(unittest.TestCase):
    def setUp(self):
        self.orig={
            "_rpc":m._rpc,
            "build_solana_recovery_plan":m.build_solana_recovery_plan,
            "load_solana_chain_checkpoint":m.load_solana_chain_checkpoint,
            "persist_solana_universal_chain_batch":m.persist_solana_universal_chain_batch,
            "commit_solana_chain_checkpoint":m.commit_solana_chain_checkpoint,
        }

    def tearDown(self):
        for k,v in self.orig.items(): setattr(m,k,v)

    def _base(self):
        m._rpc=lambda *a,**k:110
        m.build_solana_recovery_plan=lambda head,root:SimpleNamespace(gap_slots=4,start_slot=101,mode="BACKFILL")
        m.load_solana_chain_checkpoint=lambda root:SimpleNamespace(last_committed_slot=100)

    def test_four_requested_slots_are_four_independent_persistence_commits(self):
        self._base(); calls=[]; checkpoints=[]
        def persist(start,limit,root,timeout,acq):
            calls.append((start,limit))
            return SimpleNamespace(coverage_state="UNIVERSAL_BATCH_ACCOUNTED",transactions=10,observations=20,committed_events=20)
        m.persist_solana_universal_chain_batch=persist
        m.commit_solana_chain_checkpoint=lambda slot,*a,**k:checkpoints.append(slot)
        x=m.run_solana_universal_worker_cycle(".",per_batch_limit=4)
        self.assertEqual(calls,[(101,1),(102,1),(103,1),(104,1)])
        self.assertEqual(checkpoints,[101,102,103,104])
        self.assertEqual(x.after_slot,104)
        self.assertEqual(x.requested_slots,4)
        self.assertEqual(x.observations,80)
        self.assertEqual(x.state,"COMMITTED")

    def test_failure_does_not_advance_past_last_committed_slot(self):
        self._base(); checkpoints=[]; calls=[]
        def persist(start,limit,root,timeout,acq):
            calls.append((start,limit))
            if start==103: raise TimeoutError("synthetic persistence timeout")
            return SimpleNamespace(coverage_state="UNIVERSAL_BATCH_ACCOUNTED",transactions=1,observations=2,committed_events=2)
        m.persist_solana_universal_chain_batch=persist
        m.commit_solana_chain_checkpoint=lambda slot,*a,**k:checkpoints.append(slot)
        with self.assertRaises(TimeoutError):
            m.run_solana_universal_worker_cycle(".",per_batch_limit=4)
        self.assertEqual(calls,[(101,1),(102,1),(103,1)])
        self.assertEqual(checkpoints,[101,102])

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-326 single-slot durable commit foundational repair certified")
    print("[PASS] no four-block monster persistence request")
    print("[PASS] checkpoint advances only after each individually committed slot")
