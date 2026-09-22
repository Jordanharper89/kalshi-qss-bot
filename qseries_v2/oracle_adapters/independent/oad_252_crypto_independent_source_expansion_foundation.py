from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class IndependentCryptoObservation:
    source_id:str
    provider:str
    source_class:str
    subject:str
    observation_type:str
    observed_at:str
    payload:Mapping[str,Any]
    provenance_hash:str
    independent_evidence:bool=True
    execution_authority:bool=False

def build_independent_crypto_observation(
    *,
    source_id,
    provider,
    source_class,
    subject,
    observation_type,
    payload,
    observed_at=None,
):
    required=(source_id,provider,source_class,subject,observation_type)
    if not all(str(x).strip() for x in required):
        raise ValueError("source identity, provider, class, subject, and observation type are required")
    ts=str(observed_at or datetime.now(timezone.utc).isoformat())
    body={
        "source_id":str(source_id),
        "provider":str(provider),
        "source_class":str(source_class),
        "subject":str(subject),
        "observation_type":str(observation_type),
        "observed_at":ts,
        "payload":dict(payload),
    }
    h=sha256(json.dumps(body,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
    return IndependentCryptoObservation(
        str(source_id),str(provider),str(source_class),str(subject),
        str(observation_type),ts,dict(payload),h,True,False
    )

def verify_independent_crypto_observation(x):
    return (
        isinstance(x,IndependentCryptoObservation)
        and x.independent_evidence is True
        and x.execution_authority is False
        and bool(x.source_id)
        and bool(x.provider)
        and bool(x.source_class)
        and len(x.provenance_hash)==64
    )
