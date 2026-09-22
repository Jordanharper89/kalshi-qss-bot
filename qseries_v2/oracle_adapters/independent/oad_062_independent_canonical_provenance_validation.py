from dataclasses import dataclass
READ_ONLY=True
EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class ProvenanceValidation: observation_id:str; valid:bool; reason:str
def validate_independent_canonical(x):
 p=dict(x.payload); q=dict(x.provenance)
 ok=(p.get("independent_evidence") is True and p.get("source_class") in ("authoritative_real_world","independent_information")
     and str(p.get("source_url","")).startswith("http") and len(str(p.get("provenance_hash","")))==64
     and q.get("execution_authority") is False and "kalshi" not in str(x.source_id).lower())
 return ProvenanceValidation(x.observation_id,ok,"VALID_INDEPENDENT_PROVENANCE" if ok else "INVALID_OR_MARKET_DERIVED")
