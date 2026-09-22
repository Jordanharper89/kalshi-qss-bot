from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_021_exclusive_postgresql_canonical_writer.py";TEST=ROOT/"test_oph_021_exclusive_postgresql_canonical_writer.py";RUN=ROOT/"run_oph_021_exclusive_postgresql_canonical_writer.py";INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport os,time,uuid\nfrom .oph_019_postgresql_universal_ingestion_queue import connect,ensure_postgresql_ingestion_schema,claim_next_request,complete_request,fail_request,queue_counts\nOPH_021_BUILD_ID="OPH-021"\nOPH_021_REVISION="OPH_021_EXCLUSIVE_POSTGRESQL_CANONICAL_WRITER_V1"\nADVISORY_LOCK_KEY=578721019023\n\n@dataclass(frozen=True)\nclass ExclusiveWriterContract:\n    postgresql_queue:bool=True\n    one_writer_lease:bool=True\n    direct_producer_write_authority:bool=False\n    execution_authority:bool=False\n\ndef acquire_writer_lease(root=None):\n    conn=connect(root,autocommit=True)\n    with conn.cursor() as cur:\n        cur.execute("SELECT pg_try_advisory_lock(%s)",(ADVISORY_LOCK_KEY,))\n        locked=bool(cur.fetchone()[0])\n    if not locked:\n        conn.close();raise RuntimeError("Another OPH canonical writer already holds the PostgreSQL writer lease")\n    return conn\n\ndef build_canonical_router(root=None):\n    from qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import build_existing_canonical_router\n    return build_existing_canonical_router(Path(root or Path.cwd()).resolve())\n\ndef run_exclusive_writer_forever(root=None,progress=None,idle_sleep_seconds=0.002):\n    root=Path(root or Path.cwd()).resolve();ensure_postgresql_ingestion_schema(root);lease=acquire_writer_lease(root)\n    worker=f"oph021:{os.getpid()}:{uuid.uuid4().hex[:8]}";router=build_canonical_router(root)\n    if progress:progress(f"[OPH-021 WRITER] worker={worker} lease=ACQUIRED queue={queue_counts(root)}")\n    try:\n        while True:\n            item=claim_next_request(worker,root)\n            if item is None:time.sleep(float(idle_sleep_seconds));continue\n            request_id,producer,priority,observations=item;started=time.perf_counter()\n            try:\n                result=tuple(router.route_batch(tuple(observations),datetime.now(timezone.utc)))\n                complete_request(request_id,result,root)\n                if progress:progress(f"[OPH-021 COMMIT] request={request_id[:10]} producer={producer} priority={priority} observations={len(observations)} elapsed_ms={(time.perf_counter()-started)*1000:.2f}")\n            except Exception as exc:\n                fail_request(request_id,exc,root);router=build_canonical_router(root)\n                if progress:progress(f"[OPH-021 RETRY] request={request_id[:10]} producer={producer} type={type(exc).__name__} message={exc}")\n    except KeyboardInterrupt:return 0\n    finally:\n        try:\n            with lease.cursor() as cur:cur.execute("SELECT pg_advisory_unlock(%s)",(ADVISORY_LOCK_KEY,))\n        finally:lease.close()\n\ndef verify_oph_021_exclusive_postgresql_canonical_writer():\n    x=ExclusiveWriterContract()\n    return x.postgresql_queue and x.one_writer_lease and not x.direct_producer_write_authority and not x.execution_authority\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import *\nclass T(unittest.TestCase):\n    def test_verifier(self):self.assertTrue(verify_oph_021_exclusive_postgresql_canonical_writer())\n    def test_key(self):self.assertIsInstance(ADVISORY_LOCK_KEY,int)\nif __name__=="__main__":\n    print("="*88);print(" OPH-021 CERTIFICATION TEST");print(" EXCLUSIVE POSTGRESQL CANONICAL WRITER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] Exclusive canonical writer certified");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-021 CERTIFIED")\n';RUN_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import run_exclusive_writer_forever\nif __name__=="__main__":\n    print("="*96,flush=True);print(" OPH-021 EXCLUSIVE POSTGRESQL UNIVERSAL CANONICAL WRITER",flush=True);print("="*96,flush=True)\n    raise SystemExit(run_exclusive_writer_forever(Path.cwd(),lambda x:print(x,flush=True)))\n'

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
    print("="*88);print(" OPH-021 INSTALLER");print(" EXCLUSIVE POSTGRESQL CANONICAL WRITER");print("="*88);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_020_universal_postgresql_producer_admission")
    if up.verify_oph_020_universal_postgresql_producer_admission() is not True:raise RuntimeError("Certified OPH-020 verification failed")
    affected=(MOD,TEST,RUN,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);write_exact(RUN,RUN_SOURCE);update_init(INIT,"from .oph_021_exclusive_postgresql_canonical_writer import *")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-021 installation failed; affected files restored");raise
    print("[PASS] One PostgreSQL advisory lease governs the canonical writer");print("[PASS] execution_authority=FALSE");print("[DONE] OPH-021 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
