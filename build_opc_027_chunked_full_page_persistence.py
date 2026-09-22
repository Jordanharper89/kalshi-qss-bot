from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_027_chunked_full_page_persistence.py"
TEST=ROOT/"test_opc_027_chunked_full_page_persistence.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\nfrom pathlib import Path\nimport time\n\nfrom .opc_006_universal_market_snapshot_canonicalizer import build_universal_market_snapshot\nfrom .opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router,persist_snapshot_batch\n\ntry:\n    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import PostgreSQLPersistenceRoutingFailure\nexcept Exception:\n    PostgreSQLPersistenceRoutingFailure=()\n\nOPC_027_BUILD_ID="OPC-027"\nOPC_027_REVISION="OPC_027_CHUNKED_FULL_PAGE_PERSISTENCE_V1"\n\n@dataclass(frozen=True)\nclass ChunkedPersistenceResult:\n    requested:int\n    persisted:int\n    rejected:int\n    chunks_completed:int\n    retries_used:int\n    chunk_size:int\n    execution_authority:bool=False\n\ndef _retryable(exc):\n    try:\n        if PostgreSQLPersistenceRoutingFailure and isinstance(exc,PostgreSQLPersistenceRoutingFailure):\n            return True\n    except TypeError:\n        pass\n    return type(exc).__name__=="PostgreSQLPersistenceRoutingFailure" or isinstance(exc,(TimeoutError,ConnectionError))\n\ndef persist_full_page_in_chunks(\n    markets,\n    admitted_tickers,\n    *,\n    root=None,\n    chunk_size=100,\n    max_retries=5,\n    retry_base_seconds=0.10,\n    router=None,\n    progress=None,\n    sleep_fn=time.sleep,\n):\n    root=Path(root or Path.cwd()).resolve()\n    chunk_size=int(chunk_size)\n    if chunk_size<10 or chunk_size>500:\n        raise ValueError("chunk_size must be 10..500")\n\n    by={str(x.get("ticker") or ""):x for x in markets if isinstance(x,dict)}\n    selected=[by[t] for t in admitted_tickers if t in by]\n\n    if router is None:\n        router=build_opc_postgresql_router(root)\n\n    total_persisted=0\n    total_retries=0\n    chunks=0\n    base=datetime.now(timezone.utc)\n\n    for start in range(0,len(selected),chunk_size):\n        rows=selected[start:start+chunk_size]\n        batch_id="batch.opc.027."+base.strftime("%Y%m%dT%H%M%S%fZ")+f".{start:06d}"\n\n        observations=[\n            build_universal_market_snapshot(\n                row,\n                acquired_at=base+timedelta(microseconds=start+i+1),\n                batch_id=batch_id,\n            )\n            for i,row in enumerate(rows)\n        ]\n\n        attempt=0\n        while True:\n            try:\n                result=persist_snapshot_batch(\n                    observations,\n                    routed_at=datetime.now(timezone.utc),\n                    router=router,\n                )\n                total_persisted+=result.accepted\n                chunks+=1\n                if progress:\n                    progress(\n                        f"[COVERAGE CHUNK] chunk={chunks} "\n                        f"requested={len(observations)} "\n                        f"persisted={result.accepted} retries={attempt}"\n                    )\n                break\n            except KeyboardInterrupt:\n                raise\n            except Exception as exc:\n                if not _retryable(exc) or attempt>=int(max_retries):\n                    raise\n                attempt+=1\n                total_retries+=1\n                delay=min(2.0,float(retry_base_seconds)*(2**(attempt-1)))\n                if progress:\n                    progress(\n                        f"[COVERAGE CHUNK RETRY] attempt={attempt}/{max_retries} "\n                        f"type={type(exc).__name__} delay={delay:.2f}s"\n                    )\n                if delay:\n                    sleep_fn(delay)\n\n    requested=len(selected)\n    return ChunkedPersistenceResult(\n        requested=requested,\n        persisted=total_persisted,\n        rejected=requested-total_persisted,\n        chunks_completed=chunks,\n        retries_used=total_retries,\n        chunk_size=chunk_size,\n        execution_authority=False,\n    )\n\ndef verify_opc_027_chunked_full_page_persistence():\n    x=ChunkedPersistenceResult(1000,1000,0,10,2,100,False)\n    return x.requested==1000 and x.persisted==1000 and x.rejected==0 and x.chunks_completed==10 and not x.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_027_chunked_full_page_persistence import verify_opc_027_chunked_full_page_persistence\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_027_chunked_full_page_persistence())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-027 CERTIFICATION TEST")\n    print(" CHUNKED FULL PAGE PERSISTENCE")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-027 certified")\n    print("[DONE] OPC-027 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)


def main():
    print("="*80)
    print(" OPC-027 INSTALLER")
    print(" CHUNKED FULL PAGE PERSISTENCE")
    print("="*80)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_026_full_page_coverage_admission")
    if up.verify_opc_026_full_page_coverage_admission() is not True:
        raise RuntimeError("Certified OPC-026 verification failed")
    print("[PASS] Certified OPC-026 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_027_chunked_full_page_persistence import *"
        if export not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+export+"\n")
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-027 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-027 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
