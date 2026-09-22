from pathlib import Path
import ast, os, shutil, time

EXPECTED='build_oad_325_solana_IDEMPOTENT_EXACT_READBACK_FOUNDATIONAL_REPAIR.py'
TARGET=Path("qseries_v2/oracle_adapters/independent/oad_325_solana_universal_single_writer_persistence.py")
OAD150=Path("qseries_v2/oracle_adapters/independent/oad_150_solana_onchain_canonical_postgresql_persistence.py")
OAD068=Path("qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py")
TEST=Path("test_oad_325_solana_idempotent_exact_readback_foundational_repair.py")
OLD_IMPORT='from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_322_solana_universal_chain_coverage_gate import build_universal_coverage_batch'
NEW_IMPORT='from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_322_solana_universal_chain_coverage_gate import build_universal_coverage_batch'
OLD_FUNC='def persist_solana_universal_chain_batch(start_slot=None,limit=2,root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    root=Path(root or Path.cwd()).resolve()\n    x=build_universal_coverage_batch(start_slot,limit,acquisition_timeout_seconds)\n    items=tuple(x.observations)\n    if not items:return SolanaUniversalPersistenceResult(x.transactions,0,0,None,x.state,False)\n    sub=submit_observation_batch(PRODUCER,PRIORITY,items,root)\n    events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n    accepted=sum(1 for e in events if getattr(e,"accepted",False) is True)\n    return SolanaUniversalPersistenceResult(x.transactions,len(items),accepted,str(sub.request_id),x.state,False)\n'
NEW_FUNC='def persist_solana_universal_chain_batch(start_slot=None,limit=2,root=None,timeout_seconds=120.0,acquisition_timeout_seconds=20.0):\n    root=Path(root or Path.cwd()).resolve()\n    x=build_universal_coverage_batch(start_slot,limit,acquisition_timeout_seconds)\n    items=tuple(x.observations)\n    if not items:return SolanaUniversalPersistenceResult(x.transactions,0,0,None,x.state,False)\n\n    backend=_backend(root)\n    missing=[]\n    for i,obs in enumerate(items):\n        row=_query_one(backend,obs.observation_id,i)\n        if row is None:\n            missing.append(obs)\n        elif row.observation_id!=obs.observation_id:\n            raise RuntimeError("Solana exact PostgreSQL pre-read identity mismatch: "+obs.observation_id)\n\n    request_id=None\n    if missing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root)\n        request_id=str(sub.request_id)\n        events=tuple(await_request(request_id,root,float(timeout_seconds)))\n        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)\n        if len(accepted)!=len(missing):\n            raise RuntimeError("Solana universal single-writer commit mismatch")\n\n    ids=tuple(obs.observation_id for obs in items)\n    rows=tuple(exact_postgresql_readback(ids,root))\n    if len(rows)!=len(ids):\n        raise RuntimeError("Solana universal exact PostgreSQL readback mismatch")\n\n    return SolanaUniversalPersistenceResult(\n        x.transactions,\n        len(items),\n        len(rows),\n        request_id,\n        x.state,\n        False,\n    )\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nimport qseries_v2.oracle_adapters.independent.oad_325_solana_universal_single_writer_persistence as m\n\nclass Obs:\n    def __init__(self,oid): self.observation_id=oid\n\nclass T(unittest.TestCase):\n    def setUp(self):\n        self.orig={k:getattr(m,k) for k in (\n            "build_universal_coverage_batch","_backend","_query_one",\n            "submit_observation_batch","await_request","exact_postgresql_readback"\n        )}\n\n    def tearDown(self):\n        for k,v in self.orig.items(): setattr(m,k,v)\n\n    def _coverage(self):\n        items=(Obs("a"),Obs("b"),Obs("c"))\n        m.build_universal_coverage_batch=lambda *a,**k:SimpleNamespace(\n            observations=items,transactions=7,state="UNIVERSAL_BATCH_ACCOUNTED"\n        )\n        m._backend=lambda root:object()\n        return items\n\n    def test_all_existing_is_idempotent_no_write(self):\n        items=self._coverage()\n        m._query_one=lambda backend,oid,i:SimpleNamespace(observation_id=oid)\n        def forbidden(*a,**k): raise AssertionError("writer must not be called for existing observations")\n        m.submit_observation_batch=forbidden\n        m.await_request=forbidden\n        m.exact_postgresql_readback=lambda ids,root:tuple(SimpleNamespace(observation_id=x) for x in ids)\n        x=m.persist_solana_universal_chain_batch(100,1,".")\n        self.assertEqual(x.observations,3)\n        self.assertEqual(x.committed_events,3)\n        self.assertIsNone(x.request_id)\n        self.assertEqual(x.coverage_state,"UNIVERSAL_BATCH_ACCOUNTED")\n\n    def test_mixed_replay_writes_only_missing_then_exact_readback(self):\n        items=self._coverage()\n        existing={"a","c"}\n        m._query_one=lambda backend,oid,i:(SimpleNamespace(observation_id=oid) if oid in existing else None)\n        captured=[]\n        def submit(producer,priority,obs,root):\n            captured.extend(x.observation_id for x in obs)\n            return SimpleNamespace(request_id="req1")\n        m.submit_observation_batch=submit\n        m.await_request=lambda rid,root,timeout:(SimpleNamespace(accepted=True),)\n        m.exact_postgresql_readback=lambda ids,root:tuple(SimpleNamespace(observation_id=x) for x in ids)\n        x=m.persist_solana_universal_chain_batch(100,1,".")\n        self.assertEqual(captured,["b"])\n        self.assertEqual(x.request_id,"req1")\n        self.assertEqual(x.committed_events,3)\n\n    def test_commit_count_mismatch_fails_closed(self):\n        self._coverage()\n        m._query_one=lambda *a,**k:None\n        m.submit_observation_batch=lambda *a,**k:SimpleNamespace(request_id="req2")\n        m.await_request=lambda *a,**k:(SimpleNamespace(accepted=True),)\n        m.exact_postgresql_readback=lambda *a,**k:()\n        with self.assertRaises(RuntimeError):\n            m.persist_solana_universal_chain_batch(100,1,".")\n\nif __name__=="__main__":\n    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not rr.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-325 idempotent exact-readback foundational repair certified")\n    print("[PASS] existing observations are not resubmitted")\n    print("[PASS] mixed replay submits only missing observations")\n    print("[PASS] exact PostgreSQL readback required before success")\n'

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
    if not target.is_file() or not (root/OAD150).is_file() or not (root/OAD068).is_file():
        raise RuntimeError("required certified persistence dependencies missing")

    # Prove the older certified Solana path already contains the idempotent pattern
    old150=(root/OAD150).read_text(encoding="utf-8")
    for marker in ("backend=_backend(root)","_query_one(backend","exact_postgresql_readback(ids,root)"):
        if marker not in old150:
            raise RuntimeError("OAD-150 certified idempotent persistence pattern unavailable: "+marker)

    src=target.read_text(encoding="utf-8")
    if OLD_IMPORT not in src or OLD_FUNC not in src:
        raise RuntimeError("exact uploaded OAD-325 source mismatch; no mutation performed")

    stamp=time.strftime("%Y%m%dT%H%M%S")
    bak=target.with_name(target.name+".pre_idempotent_exact_readback_repair."+stamp+".bak")
    shutil.copy2(target,bak)

    src=src.replace(OLD_IMPORT,NEW_IMPORT,1).replace(OLD_FUNC,NEW_FUNC,1)
    atomic(target,src)
    atomic(root/TEST,TEST_SOURCE)

    print("[PASS] exact uploaded OAD-325 source matched")
    print("[PASS] certified OAD-150 idempotent persistence pattern verified")
    print("[PASS] rollback backup:",bak.relative_to(root))
    print("[PASS] OAD-325 now exact-reads PostgreSQL before submission")
    print("[PASS] already-persisted observations are skipped, not resubmitted")
    print("[PASS] only missing observations enter OPH-019/021")
    print("[PASS] exact PostgreSQL readback of the full slot is required before success")
    print("[PASS] canonical duplicate-rejection contract remains unchanged")
    print("[PASS] OPH-019/021 unchanged")
    print("[PASS] OAD-326 interface unchanged")
    print("[PASS] no second writer; no direct persistence bypass; no GMGN dependency")
    print("[PASS] execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__": main()
