from hashlib import sha256
import json
from qseries_v2.oracle_continuous_learner.ocl_003_outcome_observation import build_outcome_observation
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event
from qseries_v2.oracle_continuous_learner.ocl_026_continuous_intake_runtime import build_runtime_input

def _h(x):
 return sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def build_slop_learning_input(sequence,e):
 subject="solana:"+e["token_address"]
 value={"outcome":e["outcome"],"net_return":e["net_return"],
  "gross_return":e["gross_return"],"terminal_return":e["terminal_return"],
  "mfe":e["mfe"],"mae":e["mae"],"condition":"BUY_PRESSURE",
  "horizon_seconds":60,"target_fraction":.10,"stop_fraction":-.05,"friction_bps":200}
 source_hash=_h({"prediction_id":e["prediction_id"],"evidence_hash":e["evidence_hash"],"value":value})
 oo=build_outcome_observation(subject,"prospective_market_path",value,
  e["frozen_at"],"slop:"+e["prediction_id"],source_hash)
 lineage=_h({"evidence_hash":e["evidence_hash"],"source_hash":source_hash,
  "prediction_id":e["prediction_id"]})
 event=assemble_learning_event(subject,e["evidence_hash"],lineage,oo)
 ri=build_runtime_input(int(sequence),"learning_event",event.event_id,event.event_hash,
  {"subject_id":event.subject_id,"evidence_hash":event.evidence_hash,
   "outcome_hash":event.outcome_hash,"lineage_hash":event.lineage_hash,
   "outcome_type":event.outcome_type})
 return oo,event,ri
