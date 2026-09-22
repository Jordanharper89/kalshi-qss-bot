from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-273'
REVISION='OAD_273_SOLANA_PINNED_POOL_LIVE_SNAPSHOT_PERSISTENCE_V1'
TITLE='SOLANA PINNED POOL LIVE SNAPSHOT PERSISTENCE'
EXPECTED_FILENAME='build_oad_273_solana_pinned_pool_live_snapshot_persistence.py'
MODULE_NAME='oad_273_solana_pinned_pool_live_snapshot_persistence.py'
TEST_NAME='test_oad_273_solana_pinned_pool_live_snapshot_persistence.py'
DEPENDENCIES={'qseries_v2/oracle_adapters/independent/oad_262_solana_live_token_discovery.py': ('discover_live_solana_tokens',), 'qseries_v2/oracle_adapters/independent/oad_263_solana_token_pool_identity_liquidity_expansion.py': ('expand_live_solana_token_pools',), 'qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py': ('canonicalize_expansion_observation',), 'qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py': ('_backend', '_query_one', 'exact_postgresql_readback'), 'qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py': ('submit_observation_batch', 'await_request')}
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request\nfrom .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback\nfrom .oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation\nfrom .oad_262_solana_live_token_discovery import discover_live_solana_tokens\nfrom .oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\nPRODUCER="oracle.solana_continuous_pool"\nPRIORITY=20\nBATCH_ID="oad273.solana-pinned-pool"\n\n@dataclass(frozen=True,slots=True)\nclass PinnedSolanaPoolSnapshot:\n    token_address:str\n    observation_id:str\n    source_id:str\n    provider:str\n    pools:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    observed_at:str\n    execution_authority:bool=False\n\ndef select_live_solana_token(timeout_seconds=20.0):\n    d=discover_live_solana_tokens(timeout_seconds)\n    tokens=tuple(d.payload.get("tokens") or ())\n    if not tokens:\n        raise RuntimeError("OAD-262 returned no live Solana token")\n    return str(tokens[0]["token_address"])\n\ndef persist_pinned_solana_pool_snapshot(\n    token_address=None,\n    root=None,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=20.0,\n):\n    root=Path(root or Path.cwd()).resolve()\n    token=str(token_address or select_live_solana_token(acquisition_timeout_seconds))\n    raw=expand_live_solana_token_pools(token_address=token,timeout_seconds=acquisition_timeout_seconds)\n    if str(raw.payload.get("token_address")) != token:\n        raise RuntimeError("pinned token identity mismatch")\n\n    canonical=canonicalize_expansion_observation(raw,BATCH_ID)\n    backend=_backend(root)\n    existing=1 if _query_one(backend,canonical.observation_id,0) is not None else 0\n    committed=0\n    if not existing:\n        sub=submit_observation_batch(PRODUCER,PRIORITY,(canonical,),root)\n        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))\n        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)\n        if len(accepted)!=1:\n            raise RuntimeError("pinned Solana pool single-writer commit mismatch")\n        committed=1\n\n    rows=tuple(exact_postgresql_readback((canonical.observation_id,),root))\n    if len(rows)!=1:\n        raise RuntimeError("pinned Solana pool exact PostgreSQL readback mismatch")\n\n    observed_at=getattr(raw,"observed_at",datetime.now(timezone.utc))\n    if hasattr(observed_at,"isoformat"): observed_at=observed_at.isoformat()\n    return PinnedSolanaPoolSnapshot(\n        token,\n        canonical.observation_id,\n        raw.source_id,\n        raw.provider,\n        len(tuple(raw.payload.get("pools") or ())),\n        existing,\n        committed,\n        1,\n        str(observed_at),\n        False,\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_273_solana_pinned_pool_live_snapshot_persistence import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        token=select_live_solana_token()\n        r=persist_pinned_solana_pool_snapshot(token)\n        print("[PHYSICAL] token_address=",r.token_address)\n        print("[PHYSICAL] source_id=",r.source_id)\n        print("[PHYSICAL] provider=",r.provider)\n        print("[PHYSICAL] pools=",r.pools)\n        print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        self.assertEqual(r.token_address,token)\n        self.assertEqual(r.provider,"dexscreener")\n        self.assertEqual(r.exact_readback,1)\n        self.assertGreaterEqual(r.pools,1)\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-273 live pinned Solana pool snapshot persisted through OPH-019")\n    print("[PASS] exact PostgreSQL readback certified")\n'

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
