from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
EXECUTION_AUTHORITY=False

def _h(v):
    return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

@dataclass(frozen=True,slots=True)
class CryptoExperienceEvidenceLineage:
    experience_id:str
    asset:str
    evidence_hash:str
    condition_hash:str
    source_families:tuple
    market_native_metric_names:tuple
    independent_metric_names:tuple
    comparable_metric_names:tuple
    lineage_hash:str
    read_only:bool=True
    execution_authority:bool=False

def build_crypto_experience_evidence_lineage(candidate):
    source_families=tuple(sorted({x[0] for x in candidate.condition_vector}))
    market_native=tuple(sorted(x[1] for x in candidate.condition_vector if x[0]=="coinbase"))
    independent=tuple(sorted(x[1] for x in candidate.condition_vector if x[0]!="coinbase"))
    comparable=tuple(sorted(x[1] for x in candidate.temporal_vector if bool(x[5])))
    raw={
        "experience_id":candidate.experience_id,"asset":candidate.asset,
        "evidence_hash":candidate.evidence_hash,"condition_hash":candidate.condition_hash,
        "source_families":source_families,"market_native_metric_names":market_native,
        "independent_metric_names":independent,"comparable_metric_names":comparable,
        "read_only":True,"execution_authority":False,
    }
    return CryptoExperienceEvidenceLineage(
        candidate.experience_id,candidate.asset,candidate.evidence_hash,candidate.condition_hash,
        source_families,market_native,independent,comparable,_h(raw),True,False
    )

def verify_crypto_experience_evidence_lineage(x):
    raw={
        "experience_id":x.experience_id,"asset":x.asset,"evidence_hash":x.evidence_hash,
        "condition_hash":x.condition_hash,"source_families":x.source_families,
        "market_native_metric_names":x.market_native_metric_names,
        "independent_metric_names":x.independent_metric_names,
        "comparable_metric_names":x.comparable_metric_names,
        "read_only":True,"execution_authority":False,
    }
    return x.read_only and not x.execution_authority and x.lineage_hash==_h(raw)
