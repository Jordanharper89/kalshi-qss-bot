from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from qseries_v2.oracle_production_hardening.oph_020_universal_postgresql_producer_admission import verify_oph_020_universal_postgresql_producer_admission
from qseries_v2.oracle_production_hardening.oph_021_exclusive_postgresql_canonical_writer import verify_oph_021_exclusive_postgresql_canonical_writer
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
PRODUCER="oracle.independent_research";PRIORITY=20
def submit_independent_canonical_batch(observations,root=None):
    items=tuple(observations)
    if not items: raise ValueError("non-empty canonical observation batch required")
    if any(getattr(x,"execution_allowed",None) is not False for x in items): raise ValueError("execution-enabled observation rejected")
    return submit_observation_batch(PRODUCER,PRIORITY,items,Path(root or Path.cwd()).resolve())
def await_independent_commit(request_id,root=None,timeout_seconds=120.0):
    return tuple(await_request(str(request_id),Path(root or Path.cwd()).resolve(),float(timeout_seconds)))
def verify_oad_066_independent_single_writer_ingress_binding():
    return verify_oph_020_universal_postgresql_producer_admission() is True and verify_oph_021_exclusive_postgresql_canonical_writer() is True and not EXECUTION_AUTHORITY and not PROBABILITY_ENABLED
