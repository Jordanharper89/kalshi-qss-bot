from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_009_coverage_queue_migration.py";TEST=ROOT/"test_oph_009_coverage_queue_migration.py";INIT=PKG/"__init__.py"
MODULE='from __future__ import annotations\nfrom pathlib import Path\nfrom .oph_006_durable_cross_process_observation_queue import submit_observation_batch,await_request\nfrom .oph_002_priority_observation_ingestion_queue import priority_for_lane\n\nOPH_009_BUILD_ID="OPH-009"\nOPH_009_REVISION="OPH_009_COVERAGE_QUEUE_MIGRATION_V1"\n\ndef install_coverage_queue_migration(root=None,timeout_seconds=60.0):\n    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter\n    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter\n    marker="_oph009_coverage_queue_migration"\n    if getattr(cls,marker,False): return False\n    root=Path(root or Path.cwd()).resolve()\n    original=cls.route_batch\n    def queued_route(self,observations,routed_at,*args,**kwargs):\n        items=tuple(observations)\n        if not items: return original(self,items,routed_at,*args,**kwargs)\n        sub=submit_observation_batch("kalshi.coverage",priority_for_lane("COVERAGE"),items,root)\n        return await_request(sub.request_id,root,timeout_seconds)\n    cls.route_batch=queued_route\n    setattr(cls,"_oph009_original_route_batch",original)\n    setattr(cls,marker,True)\n    return True\n\ndef verify_oph_009_coverage_queue_migration():\n    return priority_for_lane("COVERAGE")==20\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_009_coverage_queue_migration import verify_oph_009_coverage_queue_migration\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_009_coverage_queue_migration())\nif __name__=="__main__":\n    print("="*80);print(" OPH-009 CERTIFICATION TEST");print(" COVERAGE QUEUE MIGRATION");print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OPH-009 certified");print("[DONE] OPH-009 CERTIFIED")\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)

def main():
    print("="*80);print(" OPH-009 INSTALLER");print(" COVERAGE QUEUE MIGRATION");print("="*80);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_008_fast_lane_queue_migration")
    if up.verify_oph_008_fast_lane_queue_migration() is not True:raise RuntimeError("OPH-008 verification failed")
    print("[PASS] Certified OPH-008 upstream boundary verified")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .oph_009_coverage_queue_migration import *"
        if ex not in cur:write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-009 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPH-009 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
