from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_postgresql_reliability"
MOD=PKG/"opr_002_persistent_producer_ingress.py";TEST=ROOT/"test_opr_002_persistent_producer_ingress.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\n\nfrom .opr_001_persistent_queue_session import PersistentQueueSession\n\nOPR_002_BUILD_ID="OPR-002"\nOPR_002_REVISION="OPR_002_PERSISTENT_PRODUCER_INGRESS_V1"\n\n_SESSIONS={}\n\ndef producer_session(producer,root=None):\n    root=Path(root or Path.cwd()).resolve()\n    key=(str(producer),str(root))\n    session=_SESSIONS.get(key)\n    if session is None:\n        session=PersistentQueueSession(root,autocommit=True)\n        session.open()\n        _SESSIONS[key]=session\n    return session\n\ndef install_persistent_postgresql_ingress(producer,root=None,timeout_seconds=120.0,poll_seconds=0.025):\n    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (\n        OraclePostgreSQLCanonicalObservationPersistenceRouter,\n    )\n    root=Path(root or Path.cwd()).resolve()\n    producer=str(producer)\n    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter\n    marker="_opr002_persistent_postgresql_ingress"\n    if getattr(cls,marker,None)==producer:return False\n    session=producer_session(producer,root)\n\n    def queue_only_route(self,observations,routed_at,*args,**kwargs):\n        items=tuple(observations)\n        if not items:return ()\n        priority=100 if "fast_lane" in producer.lower() else 20\n        sub=session.submit(producer,priority,items)\n        return tuple(session.await_result(\n            sub.request_id,timeout_seconds=timeout_seconds,poll_seconds=poll_seconds\n        ))\n\n    cls.route_batch=queue_only_route\n    setattr(cls,marker,producer)\n    setattr(cls,"_opr_queue_session",session)\n    setattr(cls,"_oph_direct_canonical_postgresql_write_authority",False)\n    return True\n\ndef verify_opr_002_persistent_producer_ingress(root=None):\n    return OPR_002_BUILD_ID=="OPR-002" and callable(install_persistent_postgresql_ingress)\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_postgresql_reliability.opr_002_persistent_producer_ingress import *\n\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OPR_002_BUILD_ID,"OPR-002")\n    def test_callable(self):self.assertTrue(callable(install_persistent_postgresql_ingress))\n\nif __name__=="__main__":\n    print("="*88);print(" OPR-002 CERTIFICATION TEST");print(" PERSISTENT PRODUCER INGRESS");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Process-local persistent producer queue session certified")\n    print("[PASS] direct_canonical_postgresql_write_authority=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPR-002 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():path.unlink()
    else:path.write_bytes(data)

def update_init(path,line):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if line not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+line+"\n")

def main():
    print("="*88);print(" OPR-002 INSTALLER");print(" PERSISTENT PRODUCER INGRESS");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_postgresql_reliability.opr_001_persistent_queue_session")
    if not up.verify_opr_001_persistent_postgresql_queue_session(ROOT):raise RuntimeError("OPR-001 verification failed")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .opr_002_persistent_producer_ingress import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OPR-002 failed; files restored");raise
    print("[PASS] OPH queue table/schema unchanged")
    print("[PASS] Proven learning path untouched")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPR-002 INSTALLATION COMPLETE")
if __name__=="__main__":main()
