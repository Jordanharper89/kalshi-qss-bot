from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import (
    CanonicalPersistenceQueryRequest,
)
from .oad_068_exact_postgresql_independent_readback import _backend
from .oad_266_solana_proven_intelligence_single_writer_postgresql_persistence import (
    persist_live_solana_proven_intelligence,
)

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SolanaHistoricalObservation:
    observation_id:str
    source_id:str
    observation_type:str
    observed_at:str
    sequence_number:int|None
    provider:str|None
    subject:str|None
    payload:dict

@dataclass(frozen=True,slots=True)
class SolanaHistoryReadback:
    refreshed:bool
    queried_sources:tuple
    queried_rows:int
    records:tuple
    current_token_address:str|None
    read_only:bool=True
    execution_authority:bool=False

def _row_payload(row):
    outer=dict(row.payload)
    inner=outer.get("observation_payload")
    return dict(inner) if isinstance(inner,(dict,tuple,list)) else outer

def _record(row):
    outer=dict(row.payload)
    return SolanaHistoricalObservation(
        str(row.observation_id),
        str(row.source_id),
        str(row.observation_type),
        row.observed_at.isoformat() if hasattr(row.observed_at,"isoformat") else str(row.observed_at),
        getattr(row,"sequence_number",None),
        outer.get("provider"),
        outer.get("subject"),
        _row_payload(row),
    )

def read_solana_proven_history(
    root=None,
    source_ids=None,
    per_source_limit=64,
    refresh=True,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=20.0,
):
    root=Path(root or Path.cwd()).resolve()
    current_token=None
    if refresh:
        live=persist_live_solana_proven_intelligence(
            root=root,
            timeout_seconds=timeout_seconds,
            acquisition_timeout_seconds=acquisition_timeout_seconds,
        )
        current_token=live.token_address
        if source_ids is None:
            source_ids=live.source_ids
    if source_ids is None:
        raise ValueError("source_ids required when refresh=False")

    backend=_backend(root)
    rows=[]
    for i,source_id in enumerate(tuple(str(x) for x in source_ids)):
        req=CanonicalPersistenceQueryRequest.by_source_id(
            query_id=f"query.oad267.solana-history.{i}",
            backend_id=backend.backend_id,
            source_id=source_id,
            limit=int(per_source_limit),
            requested_at=datetime.now(timezone.utc),
            query_metadata={
                "read_only":True,
                "build_id":"OAD-267",
                "query_mode":"bounded_exact_source_history",
            },
        )
        rows.extend(tuple(backend.query(request=req)))
    records=tuple(_record(x) for x in rows)
    records=tuple(sorted(records,key=lambda x:(
        x.source_id,
        -1 if x.sequence_number is None else int(x.sequence_number),
        x.observed_at,
        x.observation_id,
    )))
    return SolanaHistoryReadback(
        bool(refresh),
        tuple(str(x) for x in source_ids),
        len(rows),
        records,
        current_token,
        True,
        False,
    )
