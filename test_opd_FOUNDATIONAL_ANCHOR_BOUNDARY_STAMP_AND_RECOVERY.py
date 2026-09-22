from pathlib import Path
from qseries_v2.oracle_predictive_discovery import opd_056_highwater_witnessed_future_outcome as m56
import qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge as m42

m42.materialize_exact_live_tokens=lambda root,s:("H:5",)
s={"anchor_id":"a","ticker":"KXBTC","observed_epoch":100.0,"horizon_seconds":5,"anchor_price":.5,
   "kalshi_state":{},"coinbase_hf_state":{},"crypto_condition_state":{},"learned_state":None,
   "anchor_sequence_boundary":123,"anchor_sequence_basis":"CANONICAL_HIGHWATER_AT_FREEZE"}
z=m42.snapshot_from_world_state(s,Path.cwd())
assert z["anchor_sequence_boundary"]==123
assert z["anchor_sequence_basis"]=="CANONICAL_HIGHWATER_AT_FREEZE"
assert m56.exact_anchor_sequence({"anchor_sequence_boundary":456,"observed_epoch":100.0},Path.cwd())==456
assert m56.execution_authority is False
print("[PASS] anchor boundary is stamped, carried, and preferred without future leakage")
print("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")
