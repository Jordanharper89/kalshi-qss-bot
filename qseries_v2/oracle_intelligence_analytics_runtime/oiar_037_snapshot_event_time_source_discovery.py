from pathlib import Path
from .oiar_021_indexed_snapshot_identity_materializer import read_latest_indexed_snapshot_identity
OIAR_037_BUILD_ID="OIAR-037";EXECUTION_AUTHORITY=False;TIME_FIELDS=("source_open_time","source_close_time","identity_observed_at")
def discover_event_time_sources(root=None):
 p=read_latest_indexed_snapshot_identity(Path(root or Path.cwd()).resolve())
 if not p:raise RuntimeError("OIAR-037 requires persisted OIAR-021 identity snapshot")
 rows=p.get("markets") or [];counts={k:sum(1 for r in rows if str(r.get(k) or "").strip()) for k in TIME_FIELDS}
 return {"market_count":len(rows),"field_counts":counts,"preferred_close_field":"source_close_time" if counts["source_close_time"] else None,"preferred_open_field":"source_open_time" if counts["source_open_time"] else None,"execution_authority":False}
def physical_probe(root=None):
 x=discover_event_time_sources(root)
 if x["market_count"]<=0:raise RuntimeError("OIAR-037 empty identity cohort")
 return x
