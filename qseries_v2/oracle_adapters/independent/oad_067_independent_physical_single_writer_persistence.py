from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle
from qseries_v2.oracle_adapters.independent.oad_065_independent_canonical_batch_gate import build_independent_canonical_batch
from qseries_v2.oracle_adapters.independent.oad_066_independent_single_writer_ingress_binding import submit_independent_canonical_batch,await_independent_commit
READ_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False
@dataclass(frozen=True,slots=True)
class IndependentPersistenceResult:
    requested:int;committed:int;observation_ids:tuple;request_id:str;execution_authority:bool=False
def persist_fresh_independent_batch(root=None,per_source_limit=2,timeout_seconds=120.0):
    raw=acquire_independent_production_bundle(per_source_limit)
    batch=build_independent_canonical_batch(raw,"oad067.physical")
    if not batch.ready_for_existing_persistence_router: raise RuntimeError("OAD-065 batch not ready")
    sub=submit_independent_canonical_batch(batch.canonical_observations,root)
    evidence=await_independent_commit(sub.request_id,root,timeout_seconds)
    accepted=tuple(x for x in evidence if getattr(x,"accepted",False) is True)
    if len(accepted)!=len(batch.canonical_observations): raise RuntimeError("single-writer commit count mismatch")
    return IndependentPersistenceResult(len(batch.canonical_observations),len(accepted),tuple(x.observation_id for x in batch.canonical_observations),str(sub.request_id),False)
