
from __future__ import annotations
from pathlib import Path
from .oiar_042_fresh_current_cohort_identity_refresh import refresh_current_cohort_identity
from .oiar_043_current_trader_cohort_temporal_bridge import materialize_current_trader_cohort_temporal_bridge
from .oiar_044_proven_current_day_trader_snapshot import materialize_proven_current_day_snapshot

OIAR_045_BUILD_ID="OIAR-045"
OIAR_045_REVISION="OIAR_045_TEMPORAL_TRADER_REFRESH_RUNTIME_V1"
EXECUTION_AUTHORITY=False

def run_temporal_trader_refresh(root=None):
    root=Path(root or Path.cwd()).resolve()
    a=refresh_current_cohort_identity(root)
    b=materialize_current_trader_cohort_temporal_bridge(root)
    c=materialize_proven_current_day_snapshot(root)
    return {"identity_markets":a["market_count"],"bridge_markets":b["market_count"],"today_markets":c["today_markets"],"classification_counts":c["classification_counts"],"execution_authority":False}

def physical_probe(root=None):
    return run_temporal_trader_refresh(root)
