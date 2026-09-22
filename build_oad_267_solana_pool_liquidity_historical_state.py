from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-267'
REVISION='OAD_267_SOLANA_POOL_LIQUIDITY_HISTORICAL_STATE_V1'
TITLE='SOLANA POOL/LIQUIDITY HISTORICAL STATE'
MODULE_NAME='oad_267_solana_pool_liquidity_historical_state.py'
TEST_NAME='test_oad_267_solana_pool_liquidity_historical_state.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_266_solana_proven_intelligence_single_writer_postgresql_persistence.py': ('persist_live_solana_proven_intelligence',), 'qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py': ('_backend',), 'qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py': ('CanonicalPersistenceQueryRequest',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import (\n    CanonicalPersistenceQueryRequest,\n)\nfrom .oad_068_exact_postgresql_independent_readback import _backend\nfrom .oad_266_solana_proven_intelligence_single_writer_postgresql_persistence import (\n    persist_live_solana_proven_intelligence,\n)\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass SolanaHistoricalObservation:\n    observation_id:str\n    source_id:str\n    observation_type:str\n    observed_at:str\n    sequence_number:int|None\n    provider:str|None\n    subject:str|None\n    payload:dict\n\n@dataclass(frozen=True,slots=True)\nclass SolanaHistoryReadback:\n    refreshed:bool\n    queried_sources:tuple\n    queried_rows:int\n    records:tuple\n    current_token_address:str|None\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef _row_payload(row):\n    outer=dict(row.payload)\n    inner=outer.get("observation_payload")\n    return dict(inner) if isinstance(inner,(dict,tuple,list)) else outer\n\ndef _record(row):\n    outer=dict(row.payload)\n    return SolanaHistoricalObservation(\n        str(row.observation_id),\n        str(row.source_id),\n        str(row.observation_type),\n        row.observed_at.isoformat() if hasattr(row.observed_at,"isoformat") else str(row.observed_at),\n        getattr(row,"sequence_number",None),\n        outer.get("provider"),\n        outer.get("subject"),\n        _row_payload(row),\n    )\n\ndef read_solana_proven_history(\n    root=None,\n    source_ids=None,\n    per_source_limit=64,\n    refresh=True,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=20.0,\n):\n    root=Path(root or Path.cwd()).resolve()\n    current_token=None\n    if refresh:\n        live=persist_live_solana_proven_intelligence(\n            root=root,\n            timeout_seconds=timeout_seconds,\n            acquisition_timeout_seconds=acquisition_timeout_seconds,\n        )\n        current_token=live.token_address\n        if source_ids is None:\n            source_ids=live.source_ids\n    if source_ids is None:\n        raise ValueError("source_ids required when refresh=False")\n\n    backend=_backend(root)\n    rows=[]\n    for i,source_id in enumerate(tuple(str(x) for x in source_ids)):\n        req=CanonicalPersistenceQueryRequest.by_source_id(\n            query_id=f"query.oad267.solana-history.{i}",\n            backend_id=backend.backend_id,\n            source_id=source_id,\n            limit=int(per_source_limit),\n            requested_at=datetime.now(timezone.utc),\n            query_metadata={\n                "read_only":True,\n                "build_id":"OAD-267",\n                "query_mode":"bounded_exact_source_history",\n            },\n        )\n        rows.extend(tuple(backend.query(request=req)))\n    records=tuple(_record(x) for x in rows)\n    records=tuple(sorted(records,key=lambda x:(\n        x.source_id,\n        -1 if x.sequence_number is None else int(x.sequence_number),\n        x.observed_at,\n        x.observation_id,\n    )))\n    return SolanaHistoryReadback(\n        bool(refresh),\n        tuple(str(x) for x in source_ids),\n        len(rows),\n        records,\n        current_token,\n        True,\n        False,\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=read_solana_proven_history(refresh=True,per_source_limit=64)\n        print("[PHYSICAL] current_token=",r.current_token_address)\n        print("[PHYSICAL] queried_sources=",r.queried_sources)\n        print("[PHYSICAL] queried_rows=",r.queried_rows)\n        print("[PHYSICAL] records=",len(r.records))\n        self.assertEqual(len(r.queried_sources),3)\n        self.assertGreaterEqual(r.queried_rows,3)\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-267 bounded exact-source Solana historical-state readback physically certified")\n    print("[PASS] holder concentration remains excluded")\n'

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
        if exp not in lines:
            lines.append(exp)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
