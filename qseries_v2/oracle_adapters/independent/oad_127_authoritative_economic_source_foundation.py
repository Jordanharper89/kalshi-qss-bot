from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping
import json

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False
ALLOWED_PROVIDERS=("api.bls.gov","api.fiscaldata.treasury.gov")

@dataclass(frozen=True)
class AuthoritativeEconomicObservation:
    source_id: str
    provider: str
    economic_family: str
    observation_type: str
    subject: str
    observed_at: str
    source_url: str
    payload: Mapping[str,Any]
    provenance_hash: str
    independent_evidence: bool=True
    source_class: str="authoritative_real_world"
    execution_authority: bool=False

def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()

def build_economic_observation(*,source_id,provider,economic_family,observation_type,subject,observed_at,source_url,payload):
    if provider not in ALLOWED_PROVIDERS:
        raise ValueError("provider is not admitted by authoritative economic source foundation")
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),default=str)
    ph=sha256((provider+"|"+source_url+"|"+canonical).encode()).hexdigest()
    return AuthoritativeEconomicObservation(
        source_id=str(source_id),provider=provider,economic_family=str(economic_family),
        observation_type=str(observation_type),subject=str(subject),observed_at=str(observed_at),
        source_url=str(source_url),payload=dict(payload),provenance_hash=ph)

def validate_economic_observation(o):
    return (
        o.provider in ALLOWED_PROVIDERS and o.source_class=="authoritative_real_world"
        and o.independent_evidence is True and o.execution_authority is False
        and str(o.source_url).startswith("https://") and len(o.provenance_hash)==64
    )
