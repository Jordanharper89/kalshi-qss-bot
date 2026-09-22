\

from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .oad_363_solana_physical_postgresql_readback_adapter import physical_readback_probe
from .oad_364_solana_post_commit_observation_reconciliation import reconcile_post_commit_ids

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaCommittedBatchReadback:
    observation_ids:tuple
    found_ids:tuple
    missing_ids:tuple
    exact:bool
    reconciliation_state:str
    execution_authority:bool=False

def observation_id_of(obj):
    for n in ("observation_id","id","canonical_observation_id","event_id"):
        if hasattr(obj,n):
            v=getattr(obj,n)
            if v is not None: return str(v)
        if isinstance(obj,dict) and obj.get(n) is not None:
            return str(obj[n])
    if hasattr(obj,"to_dict"):
        obj=obj.to_dict()
    if hasattr(obj,"__dict__"):
        obj={k:v for k,v in vars(obj).items() if not k.startswith("_")}
    if isinstance(obj,dict):
        raw=json.dumps(obj,sort_keys=True,separators=(",",":"),default=str).encode()
        return hashlib.sha256(raw).hexdigest()
    raise RuntimeError("cannot derive stable observation id")

def verify_committed_batch_exact_readback(observations, reader=None):
    ids=tuple(observation_id_of(x) for x in observations)
    probe=physical_readback_probe(ids,reader=reader)
    rec=reconcile_post_commit_ids(ids,probe)
    return SolanaCommittedBatchReadback(
        rec.committed_ids,rec.found_ids,rec.missing_ids,
        rec.reconciliation_state=="POST_COMMIT_RECONCILED",
        rec.reconciliation_state,False
    )

