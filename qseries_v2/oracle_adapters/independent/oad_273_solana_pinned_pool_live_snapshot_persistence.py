from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
from .oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation
from .oad_262_solana_live_token_discovery import discover_live_solana_tokens
from .oad_263_solana_token_pool_identity_liquidity_expansion import expand_live_solana_token_pools

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False
PRODUCER="oracle.solana_continuous_pool"
PRIORITY=20
BATCH_ID="oad273.solana-pinned-pool"

@dataclass(frozen=True,slots=True)
class PinnedSolanaPoolSnapshot:
    token_address:str
    observation_id:str
    source_id:str
    provider:str
    pools:int
    already_present:int
    committed_new:int
    exact_readback:int
    observed_at:str
    execution_authority:bool=False

def select_live_solana_token(timeout_seconds=20.0):
    d=discover_live_solana_tokens(timeout_seconds)
    tokens=tuple(d.payload.get("tokens") or ())
    if not tokens:
        raise RuntimeError("OAD-262 returned no live Solana token")
    return str(tokens[0]["token_address"])

def persist_pinned_solana_pool_snapshot(
    token_address=None,
    root=None,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=20.0,
):
    root=Path(root or Path.cwd()).resolve()
    token=str(token_address or select_live_solana_token(acquisition_timeout_seconds))
    raw=expand_live_solana_token_pools(token_address=token,timeout_seconds=acquisition_timeout_seconds)
    if str(raw.payload.get("token_address")) != token:
        raise RuntimeError("pinned token identity mismatch")

    canonical=canonicalize_expansion_observation(raw,BATCH_ID)
    backend=_backend(root)
    existing=1 if _query_one(backend,canonical.observation_id,0) is not None else 0
    committed=0
    if not existing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,(canonical,),root)
        events=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)))
        accepted=tuple(e for e in events if getattr(e,"accepted",False) is True)
        if len(accepted)!=1:
            raise RuntimeError("pinned Solana pool single-writer commit mismatch")
        committed=1

    rows=tuple(exact_postgresql_readback((canonical.observation_id,),root))
    if len(rows)!=1:
        raise RuntimeError("pinned Solana pool exact PostgreSQL readback mismatch")

    observed_at=getattr(raw,"observed_at",datetime.now(timezone.utc))
    if hasattr(observed_at,"isoformat"): observed_at=observed_at.isoformat()
    return PinnedSolanaPoolSnapshot(
        token,
        canonical.observation_id,
        raw.source_id,
        raw.provider,
        len(tuple(raw.payload.get("pools") or ())),
        existing,
        committed,
        1,
        str(observed_at),
        False,
    )
