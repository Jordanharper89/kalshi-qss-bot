
from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID="OAD-266"
REVISION="OAD_266_SOLANA_PROVEN_INTELLIGENCE_SINGLE_WRITER_POSTGRESQL_REBUILD_V1"
MODULE_NAME="oad_266_solana_proven_intelligence_single_writer_postgresql_persistence.py"
TEST_NAME="test_oad_266_solana_proven_intelligence_single_writer_postgresql_persistence.py"

DEPENDENCIES={
    "qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py":(
        "canonicalize_expansion_observation",
    ),
    "qseries_v2/oracle_adapters/independent/oad_262_solana_live_token_discovery.py":(
        "discover_live_solana_tokens",
    ),
    "qseries_v2/oracle_adapters/independent/oad_263_solana_token_pool_identity_liquidity_expansion.py":(
        "expand_live_solana_token_pools",
    ),
    "qseries_v2/oracle_adapters/independent/oad_264_solana_token_mint_authority_supply_intelligence.py":(
        "acquire_solana_token_mint_state",
    ),
    "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py":(
        "exact_postgresql_readback",
        "_backend",
        "_query_one",
    ),
    "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py":(
        "submit_observation_batch",
        "await_request",
    ),
}

MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (\n    submit_observation_batch,\n    await_request,\n)\nfrom .oad_068_exact_postgresql_independent_readback import (\n    _backend,\n    _query_one,\n    exact_postgresql_readback,\n)\nfrom .oad_261_universal_expansion_source_single_writer_postgresql_persistence import (\n    canonicalize_expansion_observation,\n)\nfrom .oad_262_solana_live_token_discovery import discover_live_solana_tokens\nfrom .oad_263_solana_token_pool_identity_liquidity_expansion import (\n    expand_live_solana_token_pools,\n)\nfrom .oad_264_solana_token_mint_authority_supply_intelligence import (\n    acquire_solana_token_mint_state,\n)\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nPUBLICATION_ALLOWED=False\nEXECUTION_AUTHORITY=False\n\nPRODUCER="oracle.solana_proven_intelligence"\nPRIORITY=20\nACQUISITION_BATCH_ID="oad266.solana-proven-intelligence"\n\n@dataclass(frozen=True, slots=True)\nclass SolanaProvenPersistenceResult:\n    token_address:str\n    raw_observations:int\n    canonical_observations:int\n    already_present:int\n    committed_new:int\n    exact_readback:int\n    providers:tuple\n    source_ids:tuple\n    observation_ids:tuple\n    rows:tuple\n    holder_concentration_deferred:bool=True\n    execution_authority:bool=False\n\ndef acquire_proven_solana_observations(acquisition_timeout_seconds=20.0):\n    discovery=discover_live_solana_tokens(acquisition_timeout_seconds)\n    tokens=tuple(discovery.payload.get("tokens") or ())\n    if not tokens:\n        raise RuntimeError("OAD-262 returned no discovered Solana token")\n\n    token_address=str(tokens[0]["token_address"])\n    pools=expand_live_solana_token_pools(\n        token_address=token_address,\n        timeout_seconds=acquisition_timeout_seconds,\n    )\n    mint=acquire_solana_token_mint_state(\n        token_address=token_address,\n        timeout_seconds=acquisition_timeout_seconds,\n    )\n\n    if str(pools.payload.get("token_address")) != token_address:\n        raise RuntimeError("OAD-263 token identity mismatch")\n    if str(mint.payload.get("token_address")) != token_address:\n        raise RuntimeError("OAD-264 token identity mismatch")\n\n    return token_address,(discovery,pools,mint)\n\ndef persist_live_solana_proven_intelligence(\n    root=None,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=20.0,\n):\n    root=Path(root or Path.cwd()).resolve()\n    token_address,raw=acquire_proven_solana_observations(\n        acquisition_timeout_seconds=acquisition_timeout_seconds\n    )\n\n    canonical=tuple(\n        canonicalize_expansion_observation(x,ACQUISITION_BATCH_ID)\n        for x in raw\n    )\n\n    backend=_backend(root)\n    existing=0\n    missing=[]\n    for i,x in enumerate(canonical):\n        if _query_one(backend,x.observation_id,i) is None:\n            missing.append(x)\n        else:\n            existing+=1\n\n    committed=0\n    if missing:\n        submission=submit_observation_batch(\n            PRODUCER,\n            PRIORITY,\n            tuple(missing),\n            root,\n        )\n        events=tuple(\n            await_request(\n                str(submission.request_id),\n                root,\n                float(timeout_seconds),\n            )\n        )\n        accepted=tuple(\n            e for e in events\n            if getattr(e,"accepted",False) is True\n        )\n        if len(accepted) != len(missing):\n            raise RuntimeError(\n                "Solana proven-intelligence single-writer commit mismatch"\n            )\n        committed=len(accepted)\n\n    ids=tuple(x.observation_id for x in canonical)\n    rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()\n    if len(rows) != len(ids):\n        raise RuntimeError(\n            "Solana proven-intelligence exact PostgreSQL readback mismatch"\n        )\n\n    return SolanaProvenPersistenceResult(\n        token_address=token_address,\n        raw_observations=len(raw),\n        canonical_observations=len(canonical),\n        already_present=existing,\n        committed_new=committed,\n        exact_readback=len(rows),\n        providers=tuple(x.provider for x in raw),\n        source_ids=tuple(x.source_id for x in raw),\n        observation_ids=ids,\n        rows=rows,\n        holder_concentration_deferred=True,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_266_solana_proven_intelligence_single_writer_postgresql_persistence import *\n\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=persist_live_solana_proven_intelligence()\n        print("[PHYSICAL] token_address=",r.token_address)\n        print("[PHYSICAL] raw_observations=",r.raw_observations)\n        print("[PHYSICAL] canonical_observations=",r.canonical_observations)\n        print("[PHYSICAL] already_present=",r.already_present)\n        print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] exact_readback=",r.exact_readback)\n        print("[PHYSICAL] providers=",r.providers)\n        print("[PHYSICAL] source_ids=",r.source_ids)\n        print("[PHYSICAL] holder_concentration_deferred=",r.holder_concentration_deferred)\n\n        self.assertEqual(r.raw_observations,3)\n        self.assertEqual(r.canonical_observations,3)\n        self.assertEqual(r.exact_readback,3)\n        self.assertTrue(r.holder_concentration_deferred)\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-266 proven Solana intelligence persisted through OPH-019 single writer")\n    print("[PASS] exact by-observation-ID PostgreSQL readback certified")\n    print("[PASS] holder concentration remains explicitly deferred")\n    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")\n'

def locate_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
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
    print(" OAD-266 SOLANA PROVEN INTELLIGENCE SINGLE-WRITER POSTGRESQL REBUILD INSTALLER")
    print(" HOLDER CONCENTRATION EXPLICITLY DEFERRED")
    print("="*120)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",root)

    for rel,symbols in DEPENDENCIES.items():
        p=root/rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: "+rel)
        src=p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def "+symbol+"(") not in src:
                raise RuntimeError(
                    "Exact dependency symbol missing: "+rel+" -> "+symbol
                )
        print("[PASS] exact dependency verified:",rel)

    # Explicitly reject the failed holder path from this production boundary.
    if "oad_265_" in MODULE_SOURCE or "holder_concentration_intelligence" in MODULE_SOURCE:
        raise RuntimeError("OAD-266 rebuild must not depend on failed OAD-265")

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
        export="from ."+module.stem+" import *"
        if export not in lines:
            lines.append(export)
        write_checked(init,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Frozen boundary changed: "+p.name)

        print("[PASS] old unrun OAD-266 holder-dependent path retired by replacement filename")
        print("[PASS] OAD-262 token discovery admitted")
        print("[PASS] OAD-263 pool/liquidity identity admitted")
        print("[PASS] OAD-264 finalized mint/supply state admitted")
        print("[PASS] OAD-265 holder concentration excluded/deferred")
        print("[PASS] OAD-261 canonicalization contract reused exactly")
        print("[PASS] OPH-019 single-writer contract reused exactly")
        print("[PASS] OAD-068 exact readback contract reused exactly")
        print("[PASS] module installed:",module.relative_to(root))
        print("[PASS] test installed:",test.name)
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-266 REBUILD INSTALLATION COMPLETE")
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
