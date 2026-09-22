from pathlib import Path
from qseries_v2.oracle_predictive_discovery.opd_062_strict_asof_live_world_state import assemble
from qseries_v2.oracle_predictive_discovery.opd_042_live_state_to_prospective_intake_bridge import intake_world_state
from qseries_v2.oracle_predictive_discovery.opd_043_exact_durable_maturity_queue import rebuild_exact
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
HORIZONS=(5,15,30,60,300,900,3600)

def intake_anchor(anchor,state_root=None,repo_root=None,assembler=None,rebuild_queue=True):
    state_root=Path(state_root or Path.cwd());repo_root=Path(repo_root or Path.cwd())
    extra=(assembler or assemble)(anchor,repo_root)
    out=[]
    for h in HORIZONS:
        s={"anchor_id":anchor["anchor_id"],"ticker":anchor["ticker"],"observed_epoch":anchor["observed_epoch"],
           "horizon_seconds":h,"anchor_price":anchor["anchor_price"],"kalshi_state":anchor["kalshi_state"],
           "anchor_sequence_boundary":anchor.get("anchor_sequence_boundary"),
           "anchor_sequence_basis":anchor.get("anchor_sequence_basis"),
           "coinbase_hf_state":extra["coinbase_hf_state"],"crypto_condition_state":extra["crypto_condition_state"],
           "learned_state":extra["learned_state"]}
        out.append(intake_world_state(s,state_root,repo_root))
    if rebuild_queue:rebuild_exact(state_root)
    return out
