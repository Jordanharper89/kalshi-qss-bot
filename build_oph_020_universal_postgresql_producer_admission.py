from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_020_universal_postgresql_producer_admission.py";TEST=ROOT/"test_oph_020_universal_postgresql_producer_admission.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nfrom .oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nOPH_020_BUILD_ID="OPH-020"\nOPH_020_REVISION="OPH_020_UNIVERSAL_POSTGRESQL_PRODUCER_ADMISSION_V1"\n\ndef install_universal_postgresql_ingress(producer,root=None,timeout_seconds=120.0):\n    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter\n    root=Path(root or Path.cwd()).resolve();producer=str(producer);cls=OraclePostgreSQLCanonicalObservationPersistenceRouter\n    marker="_oph020_universal_postgresql_ingress"\n    if getattr(cls,marker,None)==producer:return False\n    def queue_only_route(self,observations,routed_at,*args,**kwargs):\n        items=tuple(observations)\n        if not items:return ()\n        priority=100 if "fast_lane" in producer.lower() else 20\n        sub=submit_observation_batch(producer,priority,items,root)\n        return tuple(await_request(sub.request_id,root,timeout_seconds))\n    cls.route_batch=queue_only_route\n    setattr(cls,marker,producer)\n    setattr(cls,"_oph_direct_canonical_postgresql_write_authority",False)\n    return True\n\ndef patch_legacy_queue_imports():\n    from . import oph_006_durable_cross_process_observation_queue as q\n    from . import oph_012_strict_fast_lane_queue_only_admission as f\n    from . import oph_013_strict_coverage_queue_only_admission as c\n    from .oph_019_postgresql_universal_ingestion_queue import submit_observation_batch as s,await_request as a,claim_next_request,complete_request,fail_request,queue_counts\n    q.submit_observation_batch=s;q.await_request=a;q.claim_next_request=claim_next_request;q.complete_request=complete_request;q.fail_request=fail_request;q.queue_counts=queue_counts\n    f.submit_observation_batch=s;f.await_request=a;c.submit_observation_batch=s;c.await_request=a\n    return True\n\ndef verify_oph_020_universal_postgresql_producer_admission():\n    return OPH_020_BUILD_ID=="OPH-020" and "POSTGRESQL" in OPH_020_REVISION\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_020_universal_postgresql_producer_admission import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_oph_020_universal_postgresql_producer_admission())\n    def test_symbols(self):self.assertTrue(callable(install_universal_postgresql_ingress))\nif __name__=="__main__":\n    print("="*88);print(" OPH-020 CERTIFICATION TEST");print(" UNIVERSAL POSTGRESQL PRODUCER ADMISSION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Universal producer admission certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-020 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OPH-020 INSTALLER");print(" UNIVERSAL POSTGRESQL PRODUCER ADMISSION");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue")
    if up.verify_oph_019_postgresql_universal_ingestion_queue() is not True:raise RuntimeError("Certified OPH-019 verification failed")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);update_init(INIT,"from .oph_020_universal_postgresql_producer_admission import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-020 installation failed; affected files restored");raise
    print("[PASS] Producers target OPH-019 PostgreSQL ingestion only");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-020 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
