from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping
import json

READ_ONLY=True
EXECUTION_AUTHORITY=False
PROBABILITY_ENABLED=False

@dataclass(frozen=True)
class AuthoritativeSportsObservation:
    source_id: str
    provider: str
    sport_family: str
    observation_type: str
    subject: str
    observed_at: str
    source_url: str
    payload: Mapping[str, Any]
    provenance_hash: str
    independent_evidence: bool = True
    source_class: str = "authoritative_real_world"
    execution_authority: bool = False

def utcnow_iso():
    return datetime.now(timezone.utc).isoformat()

def build_observation(*, source_id, provider, sport_family, observation_type,
                      subject, observed_at, source_url, payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    ph = sha256((provider+"|"+source_url+"|"+canonical).encode()).hexdigest()
    return AuthoritativeSportsObservation(
        source_id=source_id, provider=provider, sport_family=sport_family,
        observation_type=observation_type, subject=subject,
        observed_at=observed_at, source_url=source_url, payload=dict(payload),
        provenance_hash=ph,
    )

def validate_observation(o):
    assert o.source_class == "authoritative_real_world"
    assert o.independent_evidence is True
    assert o.execution_authority is False
    assert o.provider and o.sport_family and o.subject and o.source_url
    assert len(o.provenance_hash) == 64
    return True
