from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    submit_observation_batch,
    await_request,
)
from .oad_068_exact_postgresql_independent_readback import (
    _backend,
    _query_one,
    exact_postgresql_readback,
)
from .oad_261_universal_expansion_source_single_writer_postgresql_persistence import (
    canonicalize_expansion_observation,
)
from .oad_262_solana_live_token_discovery import discover_live_solana_tokens
from .oad_263_solana_token_pool_identity_liquidity_expansion import (
    expand_live_solana_token_pools,
)
from .oad_264_solana_token_mint_authority_supply_intelligence import (
    acquire_solana_token_mint_state,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

PRODUCER="oracle.solana_proven_intelligence"
PRIORITY=20
ACQUISITION_BATCH_ID="oad266.solana-proven-intelligence"

@dataclass(frozen=True, slots=True)
class SolanaProvenPersistenceResult:
    token_address:str
    raw_observations:int
    canonical_observations:int
    already_present:int
    committed_new:int
    exact_readback:int
    providers:tuple
    source_ids:tuple
    observation_ids:tuple
    rows:tuple
    holder_concentration_deferred:bool=True
    execution_authority:bool=False

def acquire_proven_solana_observations(acquisition_timeout_seconds=20.0):
    discovery=discover_live_solana_tokens(acquisition_timeout_seconds)
    tokens=tuple(discovery.payload.get("tokens") or ())
    if not tokens:
        raise RuntimeError("OAD-262 returned no discovered Solana token")

    token_address=str(tokens[0]["token_address"])
    pools=expand_live_solana_token_pools(
        token_address=token_address,
        timeout_seconds=acquisition_timeout_seconds,
    )
    mint=acquire_solana_token_mint_state(
        token_address=token_address,
        timeout_seconds=acquisition_timeout_seconds,
    )

    if str(pools.payload.get("token_address")) != token_address:
        raise RuntimeError("OAD-263 token identity mismatch")
    if str(mint.payload.get("token_address")) != token_address:
        raise RuntimeError("OAD-264 token identity mismatch")

    return token_address,(discovery,pools,mint)

def persist_live_solana_proven_intelligence(
    root=None,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=20.0,
):
    root=Path(root or Path.cwd()).resolve()
    token_address,raw=acquire_proven_solana_observations(
        acquisition_timeout_seconds=acquisition_timeout_seconds
    )

    canonical=tuple(
        canonicalize_expansion_observation(x,ACQUISITION_BATCH_ID)
        for x in raw
    )

    backend=_backend(root)
    existing=0
    missing=[]
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None:
            missing.append(x)
        else:
            existing+=1

    committed=0
    if missing:
        submission=submit_observation_batch(
            PRODUCER,
            PRIORITY,
            tuple(missing),
            root,
        )
        events=tuple(
            await_request(
                str(submission.request_id),
                root,
                float(timeout_seconds),
            )
        )
        accepted=tuple(
            e for e in events
            if getattr(e,"accepted",False) is True
        )
        if len(accepted) != len(missing):
            raise RuntimeError(
                "Solana proven-intelligence single-writer commit mismatch"
            )
        committed=len(accepted)

    ids=tuple(x.observation_id for x in canonical)
    rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()
    if len(rows) != len(ids):
        raise RuntimeError(
            "Solana proven-intelligence exact PostgreSQL readback mismatch"
        )

    return SolanaProvenPersistenceResult(
        token_address=token_address,
        raw_observations=len(raw),
        canonical_observations=len(canonical),
        already_present=existing,
        committed_new=committed,
        exact_readback=len(rows),
        providers=tuple(x.provider for x in raw),
        source_ids=tuple(x.source_id for x in raw),
        observation_ids=ids,
        rows=rows,
        holder_concentration_deferred=True,
        execution_authority=False,
    )
