from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

OAD_056_BUILD_ID="OAD-056"
OAD_056_REVISION="OAD_056_INDEPENDENT_SOURCE_PROVENANCE_FOUNDATION_V1"
READ_ONLY=True
EXECUTION_AUTHORITY=False

ALLOWED_SOURCE_CLASSES=("authoritative_real_world","independent_information")
FORBIDDEN_SOURCE_CLASSES=("prediction_market","kalshi_market_state","kalshi_price_derivative")

@dataclass(frozen=True, slots=True)
class IndependentObservation:
    source_id:str
    source_class:str
    observation_type:str
    subject:str
    observed_at:str
    source_url:str
    payload:dict
    provenance_hash:str
    read_only:bool=True
    execution_authority:bool=False

def build_independent_observation(*,source_id,source_class,observation_type,subject,observed_at,source_url,payload):
    if source_class not in ALLOWED_SOURCE_CLASSES:
        raise ValueError("source_class is not independently admissible")
    if not source_id or not observation_type or not subject or not source_url:
        raise ValueError("independent observation identity fields required")
    body={"source_id":source_id,"source_class":source_class,"observation_type":observation_type,
          "subject":subject,"observed_at":observed_at,"source_url":source_url,"payload":payload}
    h=sha256(json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    return IndependentObservation(source_id,source_class,observation_type,subject,observed_at,source_url,dict(payload),h)

def verify_oad_056_independent_source_provenance_foundation():
    x=build_independent_observation(source_id="test.authority",source_class="authoritative_real_world",
        observation_type="event",subject="test",observed_at="2026-08-27T00:00:00Z",
        source_url="https://example.gov/test",payload={"x":1})
    return x.read_only and not x.execution_authority and len(x.provenance_hash)==64
