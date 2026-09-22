
from __future__ import annotations
from pathlib import Path
from .oiar_021_indexed_snapshot_identity_materializer import materialize_indexed_snapshot_identity
OIAR_042_BUILD_ID="OIAR-042"
OIAR_042_REVISION="OIAR_042_FRESH_CURRENT_COHORT_IDENTITY_REFRESH_V1"
EXECUTION_AUTHORITY=False

def refresh_current_cohort_identity(root=None):
    root=Path(root or Path.cwd()).resolve()
    result=materialize_indexed_snapshot_identity(root, timeout_ms=15000)
    if int(result.get("market_count") or 0) <= 0:
        raise RuntimeError("OIAR-042 identity refresh returned zero markets")
    if result.get("plan_uses_index") is not True:
        raise RuntimeError("OIAR-042 refused non-indexed identity refresh")
    return result

def physical_probe(root=None):
    x=refresh_current_cohort_identity(root)
    return {
        "market_count":x["market_count"],
        "resolved_count":x["resolved_count"],
        "unresolved_count":x["unresolved_count"],
        "source_index":x["source_index"],
        "execution_authority":False,
    }
