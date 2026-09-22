from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_041_exact_live_token_materializer import materialize_exact_live_tokens
from qseries_v2.oracle_predictive_data.opd_032_prospective_state_intake_ledger import observe
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
REQ=("anchor_id","ticker","observed_epoch","horizon_seconds","anchor_price","kalshi_state","coinbase_hf_state","crypto_condition_state","learned_state")
FORBIDDEN={"future_target","future_return","mfe","mae","hit_plus_05","hit_minus_05","hit_plus_10","hit_minus_10","resolution_epoch"}

def snapshot_from_world_state(state_at_t,repo_root=None):
    if not isinstance(state_at_t,dict):raise TypeError("state_at_t must be dict")
    if FORBIDDEN.intersection(state_at_t):raise ValueError("POST_T_OR_OUTCOME_FIELD_REJECTED")
    if any(k not in state_at_t for k in REQ):raise ValueError("MISSING_EXACT_WORLD_STATE_FIELD")
    repo_root=Path(repo_root or Path.cwd())
    tokens=materialize_exact_live_tokens(repo_root,state_at_t)
    return {"anchor_id":state_at_t["anchor_id"],"ticker":state_at_t["ticker"],
            "observed_epoch":float(state_at_t["observed_epoch"]),"horizon_seconds":int(state_at_t["horizon_seconds"]),
            "anchor_price":state_at_t["anchor_price"],"tokens":list(tokens),
            "anchor_sequence_boundary":state_at_t.get("anchor_sequence_boundary"),
            "anchor_sequence_basis":state_at_t.get("anchor_sequence_basis")}

def intake_world_state(state_at_t,state_root=None,repo_root=None):
    state_root=Path(state_root or Path.cwd());repo_root=Path(repo_root or Path.cwd())
    return observe(snapshot_from_world_state(state_at_t,repo_root),state_root)
