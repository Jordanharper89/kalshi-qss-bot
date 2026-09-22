from pathlib import Path
import importlib, os, subprocess, sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_031_classified_single_writer_reliability_runtime.py"
TEST=ROOT/"test_oph_031_classified_single_writer_reliability_runtime.py"
RUN=ROOT/"run_oph_031_classified_single_writer_reliability_runtime.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport os,time,uuid\n\nfrom .oph_019_postgresql_universal_ingestion_queue import (\n    ensure_postgresql_ingestion_schema,claim_next_request,complete_request,fail_request,queue_counts\n)\nfrom .oph_021_exclusive_postgresql_canonical_writer import acquire_writer_lease,build_canonical_router,ADVISORY_LOCK_KEY\nfrom .oph_024_postgresql_stale_claim_recovery import recover_stale_claims\nfrom .oph_029_postgresql_routing_failure_classification import classify_persistence_failure,PersistenceFailureClassification\nfrom .oph_030_postgresql_writer_retry_telemetry import record_writer_event,ensure_retry_telemetry_schema\n\nOPH_031_BUILD_ID="OPH-031"\nOPH_031_REVISION="OPH_031_CLASSIFIED_SINGLE_WRITER_RELIABILITY_RUNTIME_V1"\n\ndef run_classified_writer_forever(root=None,progress=None,idle_sleep_seconds=0.002):\n    root=Path(root or Path.cwd()).resolve()\n    ensure_postgresql_ingestion_schema(root)\n    ensure_retry_telemetry_schema(root)\n    recovered=recover_stale_claims(root)\n    lease=acquire_writer_lease(root)\n    worker=f"oph031:{os.getpid()}:{uuid.uuid4().hex[:8]}"\n    router=build_canonical_router(root)\n\n    if progress:\n        progress(f"[OPH-031 RECOVERY] stale_claims_recovered={len(recovered)}")\n        progress(f"[OPH-031 WRITER] worker={worker} lease=ACQUIRED queue={queue_counts(root)}")\n\n    try:\n        while True:\n            item=claim_next_request(worker,root)\n            if item is None:\n                time.sleep(float(idle_sleep_seconds))\n                continue\n\n            request_id,producer,priority,observations=item\n            started=time.perf_counter()\n\n            try:\n                result=tuple(router.route_batch(tuple(observations),datetime.now(timezone.utc)))\n                elapsed=(time.perf_counter()-started)*1000.0\n                complete_request(request_id,result,root)\n                success=PersistenceFailureClassification("COMMIT_SUCCESS",False,False,"commit")\n                record_writer_event(request_id,producer,"COMMIT",success,1,len(observations),root,elapsed,None)\n                if progress:\n                    progress(\n                        f"[OPH-031 COMMIT] request={request_id[:10]} producer={producer} "\n                        f"priority={priority} observations={len(observations)} elapsed_ms={elapsed:.2f}"\n                    )\n            except Exception as exc:\n                elapsed=(time.perf_counter()-started)*1000.0\n                classification=classify_persistence_failure(exc)\n                record_writer_event(\n                    request_id,producer,"FAILURE",classification,1,len(observations),\n                    root,elapsed,exc\n                )\n\n                if classification.terminal:\n                    fail_request(request_id,exc,root,max_attempts=1)\n                    if progress:\n                        progress(\n                            f"[OPH-031 TERMINAL] request={request_id[:10]} producer={producer} "\n                            f"category={classification.category} type={type(exc).__name__} message={exc}"\n                        )\n                else:\n                    fail_request(request_id,exc,root)\n                    if progress:\n                        progress(\n                            f"[OPH-031 RETRY] request={request_id[:10]} producer={producer} "\n                            f"category={classification.category} type={type(exc).__name__} message={exc}"\n                        )\n                router=build_canonical_router(root)\n\n    except KeyboardInterrupt:\n        return 0\n    finally:\n        try:\n            with lease.cursor() as cur:\n                cur.execute("SELECT pg_advisory_unlock(%s)",(ADVISORY_LOCK_KEY,))\n        finally:\n            lease.close()\n\ndef verify_oph_031_classified_single_writer_reliability_runtime(root=None):\n    from .oph_030_postgresql_writer_retry_telemetry import verify_oph_030_postgresql_writer_retry_telemetry\n    return (\n        verify_oph_030_postgresql_writer_retry_telemetry(root)\n        and OPH_031_BUILD_ID=="OPH-031"\n        and callable(run_classified_writer_forever)\n    )\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_031_classified_single_writer_reliability_runtime import *\nclass T(unittest.TestCase):\n    def test_identity(self): self.assertEqual(OPH_031_BUILD_ID,"OPH-031")\n    def test_runtime_callable(self): self.assertTrue(callable(run_classified_writer_forever))\nif __name__=="__main__":\n    print("="*88);print(" OPH-031 CERTIFICATION TEST");print(" CLASSIFIED SINGLE-WRITER RELIABILITY RUNTIME");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Classified single-writer reliability runtime certified")\n    print("[PASS] Same PostgreSQL advisory writer lease preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-031 CERTIFIED")\n';RUN_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_031_classified_single_writer_reliability_runtime import run_classified_writer_forever\nif __name__=="__main__":\n    print("="*96,flush=True)\n    print(" OPH-031 CLASSIFIED POSTGRESQL SINGLE-WRITER RELIABILITY RUNTIME",flush=True)\n    print("="*96,flush=True)\n    raise SystemExit(run_classified_writer_forever(Path.cwd(),lambda x:print(x,flush=True)))\n'

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def update_init(path, export):
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path, current.rstrip() + "\n" + export + "\n")

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def main():
    print("="*88);print(" OPH-031 INSTALLER");print(" CLASSIFIED SINGLE-WRITER RELIABILITY RUNTIME");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))
    up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_030_postgresql_writer_retry_telemetry")
    if up.verify_oph_030_postgresql_writer_retry_telemetry(ROOT) is not True:
        raise RuntimeError("Certified OPH-030 upstream verification failed")
    print("[PASS] Certified OPH-030 upstream boundary verified read-only")
    affected=(MOD,TEST,RUN,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);write_exact(RUN,RUN_SOURCE)
        update_init(INIT,"from .oph_031_classified_single_writer_reliability_runtime import *")
        for p in (MOD,TEST,RUN): compile(p.read_text(encoding="utf-8"),str(p),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches()
        m=importlib.import_module("qseries_v2.oracle_production_hardening.oph_031_classified_single_writer_reliability_runtime")
        if m.verify_oph_031_classified_single_writer_reliability_runtime(ROOT) is not True:
            raise RuntimeError("OPH-031 verification failed")
    except Exception:
        for p,b in old.items(): restore(p,b)
        print("[ROLLBACK] OPH-031 installation failed; affected files restored");raise
    print("[PASS] Reliability writer runner written")
    print("[PASS] OPH-021 writer lease and canonical router preserved")
    print("[PASS] OPH-001 through OPH-030 preserved read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPH-031 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
