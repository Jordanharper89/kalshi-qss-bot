from __future__ import annotations
from dataclasses import dataclass
from .oad_228_snapshot_market_behavior_maturity_materialization import materialize_snapshot_behavior_maturity
from .oad_229_crypto_physical_entity_relationship_materialization import materialize_entity_relationship_state
from .oad_230_crypto_causal_narrative_physical_resolution import resolve_causal_narrative_physical_state
from .oad_221_crypto_scientific_reasoning_admission_physical_certification import certify_crypto_scientific_reasoning_admission
from .oad_222_crypto_physical_calibration_state_materialization import materialize_physical_calibration_state
from .oad_223_crypto_physical_source_reliability_state_materialization import materialize_physical_source_reliability_state

READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False

@dataclass(frozen=True,slots=True)
class SnapshotOCL029Readmission:
    as_of_sequence:int
    supplied_hashes:tuple[str,...]
    missing_state_hashes:tuple[str,...]
    calibration_state:str
    source_reliability_state:str
    causal_state:str
    narrative_state:str
    admission_state:str
    handoff_verified:bool
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False

def run_snapshot_ocl029_readmission(root=None):
    bm=materialize_snapshot_behavior_maturity(root)
    er=materialize_entity_relationship_state(root)
    cn=resolve_causal_narrative_physical_state(root)
    # Ensure snapshot-derived state families came from the same canonical cut.
    if len({bm.as_of_sequence,er.as_of_sequence,cn.as_of_sequence}) != 1:
        raise RuntimeError("Scientific Reasoning state materializers crossed as-of snapshot boundary")
    cal=materialize_physical_calibration_state(root)
    rel=materialize_physical_source_reliability_state(root)
    hashes={}
    if bm.market_behavior_state_hash:hashes["market_behavior_state_hash"]=bm.market_behavior_state_hash
    if bm.maturity_state_hash:hashes["maturity_state_hash"]=bm.maturity_state_hash
    if er.entity_relationship_state_hash:hashes["entity_relationship_state_hash"]=er.entity_relationship_state_hash
    adm=certify_crypto_scientific_reasoning_admission(certified_state_hashes=hashes)
    return SnapshotOCL029Readmission(
        bm.as_of_sequence,tuple(sorted(hashes)),tuple(adm.missing_state_hashes),
        cal.state,rel.state,cn.causal_state,cn.narrative_state,adm.state,bool(adm.handoff_verified)
    )
