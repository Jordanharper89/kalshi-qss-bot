from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from types import MappingProxyType
from .ois_001_foundation import build_intelligence_state_identity
from .ois_002_osr_intake_boundary import OSRStateIntake

OIS_003_BUILD_ID="OIS-003"
OIS_003_REVISION="OIS_003_CANONICAL_INTELLIGENCE_STATE_ASSEMBLY_V1"

@dataclass(frozen=True)
class CanonicalOracleIntelligenceState:
    state_id:str
    subject_id:str
    reasoning_state:str
    support:float
    confidence:float
    contradiction:float
    abstain:bool
    source_state_hash:str
    lineage_hash:str
    canonical_hash:str
    read_only:bool=True
    terminal_dependency:bool=False

def assemble_canonical_intelligence_state(intake,lineage_hash):
    if not isinstance(intake,OSRStateIntake):
        raise ValueError("certified OSR intake required")
    ident=build_intelligence_state_identity(intake.subject_id,intake.osr_state_hash,lineage_hash)
    raw={
        "state_id":ident.state_id,
        "subject_id":intake.subject_id,
        "reasoning_state":intake.reasoning_state,
        "support":intake.support,
        "confidence":intake.confidence,
        "contradiction":intake.contradiction,
        "abstain":intake.abstain,
        "source_state_hash":intake.osr_state_hash,
        "lineage_hash":lineage_hash,
        "read_only":True,
        "terminal_dependency":False,
    }
    digest=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return CanonicalOracleIntelligenceState(
        ident.state_id,intake.subject_id,intake.reasoning_state,intake.support,intake.confidence,
        intake.contradiction,intake.abstain,intake.osr_state_hash,lineage_hash,digest,True,False
    )

def verify_canonical_intelligence_state(x):
    raw={
        "state_id":x.state_id,
        "subject_id":x.subject_id,
        "reasoning_state":x.reasoning_state,
        "support":x.support,
        "confidence":x.confidence,
        "contradiction":x.contradiction,
        "abstain":x.abstain,
        "source_state_hash":x.source_state_hash,
        "lineage_hash":x.lineage_hash,
        "read_only":True,
        "terminal_dependency":False,
    }
    digest=sha256(json.dumps(raw,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return x.read_only and not x.terminal_dependency and x.canonical_hash==digest

def build_ois_003_certification_manifest():
    return MappingProxyType({
        "build_id":OIS_003_BUILD_ID,
        "revision":OIS_003_REVISION,
        "state":"canonical_oracle_intelligence_state",
        "terminal_dependency":False,
        "execution":False,
    })

def verify_ois_003_canonical_intelligence_state_assembly():
    from .ois_002_osr_intake_boundary import build_osr_state_intake
    i=build_osr_state_intake("btc","supported",.8,.9,.1,False,"a"*64)
    return verify_canonical_intelligence_state(assemble_canonical_intelligence_state(i,"b"*64))
