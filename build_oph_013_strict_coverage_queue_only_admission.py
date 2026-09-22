from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_013_strict_coverage_queue_only_admission.py";TEST=ROOT/"test_oph_013_strict_coverage_queue_only_admission.py";INIT=PKG/"__init__.py"
MODULE='from __future__ import annotations\nfrom pathlib import Path\n\nfrom .oph_006_durable_cross_process_observation_queue import (\n    submit_observation_batch,\n    await_request,\n)\nfrom .oph_002_priority_observation_ingestion_queue import priority_for_lane\nfrom .oph_011_persistence_provenance_ledger import append_provenance\n\nOPH_013_BUILD_ID="OPH-013"\nOPH_013_REVISION="OPH_013_STRICT_COVERAGE_QUEUE_ONLY_ADMISSION_V1"\n\ndef install_strict_coverage_queue_only(root=None,timeout_seconds=90.0):\n    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (\n        OraclePostgreSQLCanonicalObservationPersistenceRouter,\n    )\n\n    root=Path(root or Path.cwd()).resolve()\n    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter\n    marker="_oph013_strict_coverage_queue_only"\n\n    if getattr(cls,marker,False):\n        return False\n\n    def queue_only_route(self,observations,routed_at,*args,**kwargs):\n        items=tuple(observations)\n        if not items:\n            return ()\n\n        sub=submit_observation_batch(\n            "kalshi.coverage",\n            priority_for_lane("COVERAGE"),\n            items,\n            root,\n        )\n\n        append_provenance(\n            "PRODUCER_SUBMIT",\n            root,\n            producer="kalshi.coverage",\n            request_id=sub.request_id,\n            observation_count=len(items),\n            direct_postgresql_write_authority=False,\n        )\n\n        try:\n            result=await_request(\n                sub.request_id,\n                root,\n                timeout_seconds,\n            )\n        except Exception as exc:\n            append_provenance(\n                "PRODUCER_FAILURE",\n                root,\n                producer="kalshi.coverage",\n                request_id=sub.request_id,\n                exception_type=type(exc).__name__,\n                exception_message=str(exc),\n                direct_postgresql_write_authority=False,\n            )\n            raise\n\n        append_provenance(\n            "PRODUCER_SUCCESS",\n            root,\n            producer="kalshi.coverage",\n            request_id=sub.request_id,\n            observation_count=len(items),\n        )\n\n        return tuple(result)\n\n    cls.route_batch=queue_only_route\n    setattr(cls,marker,True)\n    setattr(cls,"_oph_queue_only_owner","kalshi.coverage")\n    return True\n\ndef verify_oph_013_strict_coverage_queue_only_admission():\n    return priority_for_lane("COVERAGE")==20\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_013_strict_coverage_queue_only_admission import verify_oph_013_strict_coverage_queue_only_admission\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_013_strict_coverage_queue_only_admission())\nif __name__=="__main__":\n    print("="*80);print(" OPH-013 CERTIFICATION TEST");print(" STRICT COVERAGE QUEUE ONLY ADMISSION");print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OPH-013 certified");print("[DONE] OPH-013 CERTIFIED")\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)

def main():
    print("="*80);print(" OPH-013 INSTALLER");print(" STRICT COVERAGE QUEUE ONLY ADMISSION");print("="*80);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_012_strict_fast_lane_queue_only_admission")
    if up.verify_oph_012_strict_fast_lane_queue_only_admission() is not True:raise RuntimeError("OPH-012 verification failed")
    print("[PASS] Certified OPH-012 upstream boundary verified")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .oph_013_strict_coverage_queue_only_admission import *"
        if ex not in cur:write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-013 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPH-013 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
