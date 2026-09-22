from __future__ import annotations
from pathlib import Path
from .olr_038_postgresql_outcome_evidence_linkage_ledger import _db as _link_db,TABLE as LINK_TABLE
from .olr_047_live_learning_metrics_contract import build_live_learning_metrics

OLR_048_BUILD_ID="OLR-048"
OLR_048_REVISION="OLR_048_POSTGRESQL_LIVE_LEARNING_METRICS_READ_MODEL_V1"

def read_linkage_metrics(root=None,settled_limit=100):
    root=Path(root or Path.cwd()).resolve()
    with _link_db()(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT
                COUNT(*) FILTER (WHERE matched=TRUE),
                COUNT(*) FILTER (WHERE matched=FALSE),
                COUNT(*)
              FROM (
                SELECT matched FROM public.{LINK_TABLE}
                ORDER BY recorded_at DESC
                LIMIT %s
              ) s""",(int(settled_limit),))
            matched,missing,settled=cur.fetchone()
    matched=int(matched or 0);missing=int(missing or 0);settled=int(settled or 0)
    return build_live_learning_metrics(settled,matched,missing,matched,0)

def verify_olr_048_postgresql_live_learning_metrics_read_model(root=None):
    from .olr_047_live_learning_metrics_contract import verify_olr_047_live_learning_metrics_contract
    return verify_olr_047_live_learning_metrics_contract(root) and OLR_048_BUILD_ID=="OLR-048"
