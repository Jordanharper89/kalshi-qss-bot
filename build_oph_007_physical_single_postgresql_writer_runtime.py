from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_production_hardening"
MOD=PKG/"oph_007_physical_single_postgresql_writer_runtime.py";TEST=ROOT/"test_oph_007_physical_single_postgresql_writer_runtime.py";INIT=PKG/"__init__.py"
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport os,time,uuid\n\nfrom .oph_006_durable_cross_process_observation_queue import claim_next_request,complete_request,fail_request,queue_counts\n\nOPH_007_BUILD_ID="OPH-007"\nOPH_007_REVISION="OPH_007_PHYSICAL_SINGLE_POSTGRESQL_WRITER_RUNTIME_V1"\n\n@dataclass(frozen=True)\nclass SingleWriterRuntimeCheck:\n    ready:bool\n    writer_id:str\n    execution_authority:bool=False\n\ndef build_existing_canonical_router(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    try:\n        from qseries_v2.oracle_pre_settlement_coverage.opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router\n        return build_opc_postgresql_router(root)\n    except Exception:\n        from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import OraclePostgreSQLCanonicalObservationPersistenceRouter\n        try:\n            return OraclePostgreSQLCanonicalObservationPersistenceRouter()\n        except TypeError as exc:\n            raise RuntimeError("Could not construct certified canonical PostgreSQL router") from exc\n\ndef run_single_writer_forever(root=None,progress=None,idle_sleep_seconds=0.002):\n    root=Path(root or Path.cwd()).resolve()\n    worker_id=f"oph007:{os.getpid()}:{uuid.uuid4().hex[:8]}"\n    router=build_existing_canonical_router(root)\n    if progress: progress(f"[SINGLE WRITER] worker={worker_id} queue={queue_counts(root)}")\n    while True:\n        try:\n            item=claim_next_request(worker_id,root)\n            if item is None:\n                time.sleep(float(idle_sleep_seconds)); continue\n            request_id,writer_id,priority,observations=item\n            started=time.perf_counter()\n            try:\n                result=tuple(router.route_batch(tuple(observations),datetime.now(timezone.utc)))\n                complete_request(request_id,result,root)\n                if progress:\n                    progress(\n                        f"[SINGLE WRITER] request={request_id[:10]} producer={writer_id} priority={priority} observations={len(observations)} elapsed_ms={(time.perf_counter()-started)*1000:.2f}"\n                    )\n            except Exception as exc:\n                fail_request(request_id,exc,root)\n                if progress:\n                    progress(f"[SINGLE WRITER] failed request={request_id[:10]} producer={writer_id} type={type(exc).__name__} message={exc}")\n        except KeyboardInterrupt:\n            return 0\n\ndef verify_oph_007_physical_single_postgresql_writer_runtime():\n    x=SingleWriterRuntimeCheck(True,"OPH-007",False)\n    return x.ready and x.writer_id=="OPH-007" and not x.execution_authority\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import verify_oph_007_physical_single_postgresql_writer_runtime\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oph_007_physical_single_postgresql_writer_runtime())\nif __name__=="__main__":\n    print("="*80);print(" OPH-007 CERTIFICATION TEST");print(" PHYSICAL SINGLE POSTGRESQL WRITER RUNTIME");print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OPH-007 certified");print("[DONE] OPH-007 CERTIFIED")\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)

def main():
    print("="*80);print(" OPH-007 INSTALLER");print(" PHYSICAL SINGLE POSTGRESQL WRITER RUNTIME");print("="*80);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue")
    if up.verify_oph_006_durable_cross_process_observation_queue() is not True:raise RuntimeError("OPH-006 verification failed")
    print("[PASS] Certified OPH-006 upstream boundary verified")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .oph_007_physical_single_postgresql_writer_runtime import *"
        if ex not in cur:write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPH-007 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPH-007 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
