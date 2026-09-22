from datetime import datetime,timezone
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
READ_ONLY=True
EXECUTION_AUTHORITY=False
def _dt(v):
    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
def canonicalize_independent_observation(x,acquisition_batch_id):
    if x.source_class not in ("authoritative_real_world","independent_information"): raise ValueError("independent source required")
    raw=RawSourceObservation.create(source_observation_id="independent."+x.source_id+"."+x.provenance_hash,
      observed_at=_dt(x.observed_at),observation_type=x.observation_type,
      payload={"subject":x.subject,"source_url":x.source_url,"source_class":x.source_class,"independent_evidence":True,
               "provenance_hash":x.provenance_hash,"source_payload":dict(x.payload)},
      provenance={"source_id":"source.independent."+x.source_id,"upstream_source_id":x.source_id,"source_class":x.source_class,
                  "source_url":x.source_url,"provenance_hash":x.provenance_hash,"read_only":True,"execution_authority":False})
    return CanonicalObservation.create(source_id="source.independent."+x.source_id,raw_observation=raw,
      acquired_at=datetime.now(timezone.utc),acquisition_batch_id=str(acquisition_batch_id))
def canonicalize_independent_bundle(report,acquisition_batch_id):
    return tuple(canonicalize_independent_observation(x,acquisition_batch_id) for x in report.observations)
