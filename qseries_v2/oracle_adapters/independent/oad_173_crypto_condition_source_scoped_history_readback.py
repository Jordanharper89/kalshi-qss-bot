from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import CanonicalPersistenceQueryRequest
from .oad_068_exact_postgresql_independent_readback import _backend
from .oad_168_crypto_condition_state_normalization import CryptoConditionState
from .oad_172_crypto_condition_snapshot_postgresql_persistence import SOURCE_PREFIX

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False
DEFAULT_PER_SOURCE_LIMIT=512

@dataclass(frozen=True,slots=True)
class CryptoConditionSourceHistory:
    queried_sources:int
    queried_rows:int
    condition_rows:int
    states:tuple
    read_only:bool=True

def condition_source_id(asset,source_family,metric_name):
    metric=str(metric_name).replace(" ","_").lower()
    family=str(source_family).replace(" ","_").lower()
    return f"{SOURCE_PREFIX}{str(asset).lower()}.{family}.{metric}"

def _state(row):
    if row.observation_type!="crypto_condition_snapshot": return None
    p=dict(row.payload)
    return CryptoConditionState(
        str(p["asset"]),str(p["source_family"]),str(p["metric_name"]),float(p["value"]),
        str(p["unit"]),str(p["condition"]),str(p["basis"]),
        bool(p["independent_evidence"]),bool(p["market_native_reference"]),
        row.observed_at.isoformat(),
    )

def read_crypto_condition_history_for_current_states(current_states,root=None,per_source_limit=DEFAULT_PER_SOURCE_LIMIT):
    root=Path(root or Path.cwd()).resolve()
    backend=_backend(root)
    source_ids=tuple(sorted({
        condition_source_id(x.asset,x.source_family,x.metric_name) for x in tuple(current_states)
    }))
    rows=[]
    for i,sid in enumerate(source_ids):
        req=CanonicalPersistenceQueryRequest.by_source_id(
            query_id=f"query.oad173.source.{i}.{sid[-32:]}",
            backend_id=backend.backend_id,
            source_id=sid,
            limit=int(per_source_limit),
            requested_at=datetime.now(timezone.utc),
            query_metadata={"read_only":True,"build_id":"OAD-173","query_mode":"exact_source_scoped_history"},
        )
        rows.extend(tuple(backend.query(request=req)))
    states=tuple(x for x in (_state(r) for r in rows) if x is not None)
    states=tuple(sorted(states,key=lambda x:(str(x.observed_at),x.asset,x.source_family,x.metric_name)))
    return CryptoConditionSourceHistory(len(source_ids),len(rows),len(states),states,True)
