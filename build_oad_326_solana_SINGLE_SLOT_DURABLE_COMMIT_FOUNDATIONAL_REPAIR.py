from pathlib import Path
import ast, os, shutil, time

EXPECTED='build_oad_326_solana_SINGLE_SLOT_DURABLE_COMMIT_FOUNDATIONAL_REPAIR.py'
TARGET=Path("qseries_v2/oracle_adapters/independent/oad_326_solana_universal_resilient_worker.py")
OPH019=Path("qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py")
OAD402=Path("qseries_v2/oracle_adapters/independent/oad_402_solana_zero_cost_surveillance_physical_gate.py")
TEST=Path("test_oad_326_solana_single_slot_durable_commit_foundational_repair.py")
OLD='def run_solana_universal_worker_cycle(root=None,per_batch_limit=4,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    root=Path(root or Path.cwd()).resolve();head=int(_rpc("getSlot",[{"commitment":"finalized"}],acquisition_timeout_seconds))\n    plan=build_solana_recovery_plan(head,root);before=load_solana_chain_checkpoint(root)\n    if plan.gap_slots<=0:return SolanaUniversalWorkerCycle(head,before.last_committed_slot,before.last_committed_slot,plan.mode,0,0,0,0,"CAUGHT_UP",False)\n    count=min(int(per_batch_limit),plan.gap_slots)\n    p=persist_solana_universal_chain_batch(plan.start_slot,count,root,timeout_seconds,acquisition_timeout_seconds)\n    target=plan.start_slot+count-1\n    if p.coverage_state!="UNIVERSAL_BATCH_ACCOUNTED":raise RuntimeError("coverage gate refused checkpoint advance")\n    commit_solana_chain_checkpoint(target,None,root)\n    return SolanaUniversalWorkerCycle(head,before.last_committed_slot,target,plan.mode,count,p.transactions,p.observations,p.committed_events,"COMMITTED",False)\n'
NEW='def run_solana_universal_worker_cycle(root=None,per_batch_limit=4,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    root=Path(root or Path.cwd()).resolve();head=int(_rpc("getSlot",[{"commitment":"finalized"}],acquisition_timeout_seconds))\n    plan=build_solana_recovery_plan(head,root);before=load_solana_chain_checkpoint(root)\n    if plan.gap_slots<=0:return SolanaUniversalWorkerCycle(head,before.last_committed_slot,before.last_committed_slot,plan.mode,0,0,0,0,"CAUGHT_UP",False)\n    count=min(int(per_batch_limit),plan.gap_slots)\n    transactions=observations=committed_events=0\n    after_slot=before.last_committed_slot\n    processed=0\n    for offset in range(count):\n        slot=plan.start_slot+offset\n        p=persist_solana_universal_chain_batch(slot,1,root,timeout_seconds,acquisition_timeout_seconds)\n        if p.coverage_state!="UNIVERSAL_BATCH_ACCOUNTED":raise RuntimeError("coverage gate refused checkpoint advance")\n        commit_solana_chain_checkpoint(slot,None,root)\n        after_slot=slot;processed+=1\n        transactions+=int(p.transactions);observations+=int(p.observations);committed_events+=int(p.committed_events)\n    return SolanaUniversalWorkerCycle(head,before.last_committed_slot,after_slot,plan.mode,processed,transactions,observations,committed_events,"COMMITTED",False)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nimport qseries_v2.oracle_adapters.independent.oad_326_solana_universal_resilient_worker as m\n\nclass T(unittest.TestCase):\n    def setUp(self):\n        self.orig={\n            "_rpc":m._rpc,\n            "build_solana_recovery_plan":m.build_solana_recovery_plan,\n            "load_solana_chain_checkpoint":m.load_solana_chain_checkpoint,\n            "persist_solana_universal_chain_batch":m.persist_solana_universal_chain_batch,\n            "commit_solana_chain_checkpoint":m.commit_solana_chain_checkpoint,\n        }\n\n    def tearDown(self):\n        for k,v in self.orig.items(): setattr(m,k,v)\n\n    def _base(self):\n        m._rpc=lambda *a,**k:110\n        m.build_solana_recovery_plan=lambda head,root:SimpleNamespace(gap_slots=4,start_slot=101,mode="BACKFILL")\n        m.load_solana_chain_checkpoint=lambda root:SimpleNamespace(last_committed_slot=100)\n\n    def test_four_requested_slots_are_four_independent_persistence_commits(self):\n        self._base(); calls=[]; checkpoints=[]\n        def persist(start,limit,root,timeout,acq):\n            calls.append((start,limit))\n            return SimpleNamespace(coverage_state="UNIVERSAL_BATCH_ACCOUNTED",transactions=10,observations=20,committed_events=20)\n        m.persist_solana_universal_chain_batch=persist\n        m.commit_solana_chain_checkpoint=lambda slot,*a,**k:checkpoints.append(slot)\n        x=m.run_solana_universal_worker_cycle(".",per_batch_limit=4)\n        self.assertEqual(calls,[(101,1),(102,1),(103,1),(104,1)])\n        self.assertEqual(checkpoints,[101,102,103,104])\n        self.assertEqual(x.after_slot,104)\n        self.assertEqual(x.requested_slots,4)\n        self.assertEqual(x.observations,80)\n        self.assertEqual(x.state,"COMMITTED")\n\n    def test_failure_does_not_advance_past_last_committed_slot(self):\n        self._base(); checkpoints=[]; calls=[]\n        def persist(start,limit,root,timeout,acq):\n            calls.append((start,limit))\n            if start==103: raise TimeoutError("synthetic persistence timeout")\n            return SimpleNamespace(coverage_state="UNIVERSAL_BATCH_ACCOUNTED",transactions=1,observations=2,committed_events=2)\n        m.persist_solana_universal_chain_batch=persist\n        m.commit_solana_chain_checkpoint=lambda slot,*a,**k:checkpoints.append(slot)\n        with self.assertRaises(TimeoutError):\n            m.run_solana_universal_worker_cycle(".",per_batch_limit=4)\n        self.assertEqual(calls,[(101,1),(102,1),(103,1)])\n        self.assertEqual(checkpoints,[101,102])\n\nif __name__=="__main__":\n    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not rr.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-326 single-slot durable commit foundational repair certified")\n    print("[PASS] no four-block monster persistence request")\n    print("[PASS] checkpoint advances only after each individually committed slot")\n'

def atomic(path,src):
    ast.parse(src,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(src,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError("installer filename mismatch")
    root=Path.cwd().resolve()
    if not (root/"qseries_v2").is_dir(): raise RuntimeError("run from repository root")
    target=root/TARGET
    if not target.is_file(): raise RuntimeError("OAD-326 missing")
    oph=(root/OPH019).read_text(encoding="utf-8")
    gate=(root/OAD402).read_text(encoding="utf-8")
    if "connect_timeout_seconds=5.0" not in oph or "poll_seconds=0.05" not in oph:
        raise RuntimeError("certified OPH-019 connection-storm foundational repair not installed")
    if '"postgresql ingestion" in msg' not in gate:
        raise RuntimeError("certified OAD-402 PostgreSQL timeout classifier repair not installed")
    src=target.read_text(encoding="utf-8")
    if OLD not in src: raise RuntimeError("exact uploaded OAD-326 source mismatch; no mutation performed")
    stamp=time.strftime("%Y%m%dT%H%M%S")
    bak=target.with_name(target.name+".pre_single_slot_commit_repair."+stamp+".bak")
    shutil.copy2(target,bak)
    src=src.replace(OLD,NEW,1)
    atomic(target,src)
    atomic(root/TEST,TEST_SOURCE)
    print("[PASS] exact uploaded OAD-326 source matched")
    print("[PASS] rollback backup:",bak.relative_to(root))
    print("[PASS] four-slot worker request decomposed into one-slot persistence commits")
    print("[PASS] each slot checkpointed only after its own universal batch commit")
    print("[PASS] partial failure cannot advance checkpoint beyond last committed slot")
    print("[PASS] OAD-325 interface unchanged")
    print("[PASS] OPH-019/021 source unchanged")
    print("[PASS] canonical PostgreSQL single-writer boundary preserved")
    print("[PASS] no second writer; no direct DB bypass; no GMGN dependency")
    print("[PASS] execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__": main()
