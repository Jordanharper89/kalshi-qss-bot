from __future__ import annotations
from dataclasses import dataclass
import importlib
REQUIRED={
"calibration_state_hash":("qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning","verify_ocl_006_probability_calibration_learning"),
"source_reliability_state_hash":("qseries_v2.oracle_continuous_learner.ocl_007_source_reliability","verify_ocl_007_source_reliability_learning"),
"market_behavior_state_hash":("qseries_v2.oracle_continuous_learner.ocl_012_market_behavior_learning","verify_ocl_012_market_behavior_learning_engine"),
"causal_state_hash":("qseries_v2.oracle_continuous_learner.ocl_014_causal_evidence","verify_ocl_014_causal_evidence_learning"),
"narrative_state_hash":("qseries_v2.oracle_continuous_learner.ocl_019_narrative_market_relationship","verify_ocl_019_narrative_market_relationship_learning"),
"entity_relationship_state_hash":("qseries_v2.oracle_continuous_learner.ocl_017_entity_relationship","verify_ocl_017_entity_relationship_learning"),
"maturity_state_hash":("qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity","verify_ocl_022_learning_confidence_evidence_maturity"),
"adaptive_weight_state_hash":("qseries_v2.oracle_continuous_learner.ocl_024_adaptive_learning_weight","verify_ocl_024_adaptive_learning_weight_model")}
@dataclass(frozen=True)
class ContractResolution:
 certified_contracts:tuple[str,...];unavailable_contracts:tuple[str,...];physical_ready:bool
def resolve_certified_ocl_contracts():
 ok=[];bad=[]
 for n,(mod,v) in REQUIRED.items():
  try:
   m=importlib.import_module(mod);(ok if getattr(m,v)() is True else bad).append(n)
  except Exception:bad.append(n)
 return ContractResolution(tuple(ok),tuple(bad),not bad)
