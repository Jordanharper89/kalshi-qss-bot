from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_033_prospective_future_outcome_resolver import resolve
execution_authority=False
REQ=("state_id","resolution_epoch","future_return","mfe","mae","hit_plus_05","hit_minus_05","hit_plus_10","hit_minus_10")
def resolve_exact(outcome,state_root=None):
 if not isinstance(outcome,dict) or any(k not in outcome for k in REQ):raise ValueError("MISSING_REQUIRED_OUTCOME_FIELD")
 return resolve(outcome,Path(state_root or Path.cwd()))
