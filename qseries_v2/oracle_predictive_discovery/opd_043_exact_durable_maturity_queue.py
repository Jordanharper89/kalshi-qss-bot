from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_039_durable_horizon_maturity_queue import rebuild,mature
execution_authority=False
def rebuild_exact(state_root=None):return rebuild(Path(state_root or Path.cwd()))
def mature_exact(state_root=None,now=None):
 rows=mature(Path(state_root or Path.cwd()),now)
 req={"state_id","ticker","observed_epoch","horizon_seconds","maturity_epoch","anchor_price","matched_family_ids"}
 if any(not isinstance(x,dict) or not req.issubset(x) for x in rows):raise RuntimeError("OPD039_MATURITY_SCHEMA_MISMATCH")
 return rows
