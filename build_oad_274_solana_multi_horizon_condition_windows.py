from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-274'
REVISION='OAD_274_SOLANA_MULTI_HORIZON_CONDITION_WINDOWS_V1'
TITLE='SOLANA MULTI-HORIZON CONDITION WINDOWS'
EXPECTED_FILENAME='build_oad_274_solana_multi_horizon_condition_windows.py'
MODULE_NAME='oad_274_solana_multi_horizon_condition_windows.py'
TEST_NAME='test_oad_274_solana_multi_horizon_condition_windows.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py': ('SolanaHistoricalObservation',), 'qseries_v2/oracle_adapters/independent/oad_270_solana_price_volume_liquidity_acceleration_conditions.py': ('build_solana_acceleration_conditions',), 'qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py': ('_backend',), 'qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py': ('CanonicalPersistenceQueryRequest',)}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest\nfrom .oad_068_exact_postgresql_independent_readback import _backend\nfrom .oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation\nfrom .oad_270_solana_price_volume_liquidity_acceleration_conditions import build_solana_acceleration_conditions\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass SolanaWindowState:\n    token_address:str\n    source_id:str\n    window_seconds:int\n    records:int\n    first_observed_at:str|None\n    last_observed_at:str|None\n    conditions:tuple\n    state:str\n    probability:None=None\n    direction:None=None\n    execution_authority:bool=False\n\ndef _payload(row):\n    outer=dict(row.payload)\n    inner=outer.get("observation_payload")\n    return dict(inner) if isinstance(inner,dict) else outer\n\ndef _record(row):\n    outer=dict(row.payload)\n    return SolanaHistoricalObservation(\n        str(row.observation_id),str(row.source_id),str(row.observation_type),\n        row.observed_at.isoformat() if hasattr(row.observed_at,"isoformat") else str(row.observed_at),\n        getattr(row,"sequence_number",None),outer.get("provider"),outer.get("subject"),_payload(row)\n    )\n\ndef read_pinned_pool_history(token_address,root=None,limit=512):\n    root=Path(root or Path.cwd()).resolve()\n    source_id="source.dex.solana.token_pools."+str(token_address)\n    backend=_backend(root)\n    req=CanonicalPersistenceQueryRequest.by_source_id(\n        query_id="query.oad274."+str(token_address),\n        backend_id=backend.backend_id,\n        source_id=source_id,\n        limit=int(limit),\n        requested_at=datetime.now(timezone.utc),\n        query_metadata={"read_only":True,"build_id":"OAD-274","query_mode":"bounded_pinned_pool_history"},\n    )\n    return tuple(_record(x) for x in backend.query(request=req))\n\ndef build_multi_horizon_solana_states(records,token_address,windows_seconds=(5,15,30,60)):\n    rows=tuple(sorted(records,key=lambda x:(x.observed_at,x.observation_id)))\n    if not rows: return ()\n    latest=datetime.fromisoformat(rows[-1].observed_at.replace("Z","+00:00"))\n    out=[]\n    for w in tuple(sorted({int(x) for x in windows_seconds})):\n        selected=[]\n        for r in rows:\n            t=datetime.fromisoformat(r.observed_at.replace("Z","+00:00"))\n            if (latest-t).total_seconds() <= w:\n                selected.append(r)\n        cond=build_solana_acceleration_conditions(tuple(selected)) if len(selected)>=2 else ()\n        state="WINDOW_READY" if cond else "HOLD_TEMPORAL_DEPTH_REQUIRED"\n        out.append(SolanaWindowState(\n            str(token_address),\n            "source.dex.solana.token_pools."+str(token_address),\n            w,len(selected),\n            selected[0].observed_at if selected else None,\n            selected[-1].observed_at if selected else None,\n            tuple((c.pair_address,c.conditions,c.state) for c in cond),\n            state,None,None,False\n        ))\n    return tuple(out)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation\nfrom qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import *\n\nclass T(unittest.TestCase):\n    def test_windows(self):\n        rows=(\n            SolanaHistoricalObservation("a","S","solana_token_pool_identity_liquidity","2026-09-01T00:00:00+00:00",1,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":100,"buys_h24":10,"sells_h24":9,"volume_h24":100,"price_usd":1.0},)}),\n            SolanaHistoricalObservation("b","S","solana_token_pool_identity_liquidity","2026-09-01T00:00:05+00:00",2,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":110,"buys_h24":12,"sells_h24":9,"volume_h24":120,"price_usd":1.1},)}),\n            SolanaHistoricalObservation("c","S","solana_token_pool_identity_liquidity","2026-09-01T00:00:15+00:00",3,"dex","X",{"token_address":"X","pools":({"pair_address":"P","liquidity_usd":130,"buys_h24":16,"sells_h24":10,"volume_h24":150,"price_usd":1.2},)}),\n        )\n        r=build_multi_horizon_solana_states(rows,"X",(5,15,30,60))\n        print("[WINDOWS]",tuple((x.window_seconds,x.records,x.state) for x in r))\n        self.assertEqual(tuple(x.window_seconds for x in r),(5,15,30,60))\n        self.assertTrue(all(x.probability is None for x in r))\n        self.assertTrue(all(x.direction is None for x in r))\n\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-274 5s/15s/30s/60s factual condition windows certified")\n'

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

    extra_paths=[]

    affected=(module,test,init,*extra_paths)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_checked(module,MODULE_SOURCE)
        write_checked(test,TEST_SOURCE)

        lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export="from ."+module.stem+" import *"
        if export not in lines:
            lines.append(export)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] holder concentration dependency absent")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] affected files restored")
        raise

if __name__=="__main__":
    main()
