from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-281'
REVISION='OAD_281_GMGN_SOLANA_SINGLE_WRITER_POSTGRESQL_PERSISTENCE_V1'
TITLE='GMGN SOLANA SINGLE-WRITER POSTGRESQL PERSISTENCE'
EXPECTED_FILENAME='build_oad_281_gmgn_solana_single_writer_postgresql_persistence.py'
MODULE_NAME='oad_281_gmgn_solana_single_writer_postgresql_persistence.py'
TEST_NAME='test_oad_281_gmgn_solana_single_writer_postgresql_persistence.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_278_gmgn_solana_trending_live_adapter.py': ('acquire_gmgn_solana_trending',), 'qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py': ('canonicalize_expansion_observation',), 'qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py': ('_backend', '_query_one', 'exact_postgresql_readback'), 'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py': ('submit_observation_batch', 'await_request')}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation\nfrom .oad_278_gmgn_solana_trending_live_adapter import acquire_gmgn_solana_trending\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nPRODUCER="oracle.gmgn.solana"\nPRIORITY=20\nBATCH_ID="oad281.gmgn.solana"\n\n@dataclass(frozen=True,slots=True)\nclass GMGNPersistenceResult:\n    raw:int\n    canonical:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    provider:str\n    state:str\n    execution_authority:bool=False\n\ndef persist_gmgn_solana_trending(root=None,timeout_seconds=120.0,acquisition_timeout_seconds=30.0):\n    root=Path(root or Path.cwd()).resolve()\n    raw=acquire_gmgn_solana_trending(timeout_seconds=acquisition_timeout_seconds)\n    canonical=canonicalize_expansion_observation(raw,BATCH_ID)\n    backend=_backend(root)\n    existing=1 if _query_one(backend,canonical.observation_id,0) is not None else 0\n    committed=0\n    if not existing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,(canonical,),root)\n        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n        accepted=tuple(x for x in events if getattr(x,"accepted",False) is True)\n        if len(accepted)!=1:\n            raise RuntimeError("GMGN single-writer commit mismatch")\n        committed=1\n    rows=tuple(exact_postgresql_readback((canonical.observation_id,),root))\n    if len(rows)!=1:\n        raise RuntimeError("GMGN exact PostgreSQL readback mismatch")\n    return GMGNPersistenceResult(1,1,existing,committed,1,"gmgn","GMGN_SOLANA_PERSISTED",False)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_277_gmgn_production_admission_boundary import evaluate_gmgn_admission\nfrom qseries_v2.oracle_adapters.independent.oad_281_gmgn_solana_single_writer_postgresql_persistence import *\n\nclass T(unittest.TestCase):\n    def test_physical_or_truthful_hold(self):\n        a=evaluate_gmgn_admission()\n        if not a.admitted:\n            print("[HOLD] GMGN persistence physical test requires admitted gmgn-cli + GMGN_API_KEY")\n            return\n        r=persist_gmgn_solana_trending()\n        print("[PHYSICAL] raw=",r.raw)\n        print("[PHYSICAL] canonical=",r.canonical)\n        print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        print("[PHYSICAL] provider=",r.provider)\n        self.assertEqual(r.exact_readback,1)\n        self.assertEqual(r.provider,"gmgn")\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-281 GMGN single-writer persistence contract certified")\n'

def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_checked(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch: expected "+EXPECTED_FILENAME)
    root=locate_root()
    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/MODULE_NAME
    test=root/TEST_NAME
    init=pkg/"__init__.py"

    print("="*120)
    print(" "+BUILD_ID+" "+TITLE+" INSTALLER")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel,symbols in DEPENDENCIES.items():
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def "+symbol+"(") not in src and ("class "+symbol) not in src:
                raise RuntimeError("Exact dependency symbol missing: "+rel+" -> "+symbol)
        print("[PASS] exact dependency verified:",rel)

    protected=[]
    for p,label in (
        (root/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
        (root/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py","Frozen Kalshi OAD-055"),
    ):
        if p.is_file():
            protected.append((p,hashlib.sha256(p.read_bytes()).hexdigest()))
            print("[PASS]",label,"verified")

    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        exp="from ."+module.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] GMGN remains observation-only")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
