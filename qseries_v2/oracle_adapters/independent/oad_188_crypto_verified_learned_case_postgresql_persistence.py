from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import RawSourceObservation,CanonicalObservation
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch,await_request
from qseries_v2.oracle_continuous_learner.ocl_004_learning_event import assemble_learning_event,verify_learning_event
from .oad_068_exact_postgresql_independent_readback import _backend,_query_one,exact_postgresql_readback
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
PRODUCER='oracle.crypto_verified_learning';PRIORITY=20;SOURCE_PREFIX='source.crypto.learned_case.'
@dataclass(frozen=True,slots=True)
class LearnedCasePersistence: cases:int;already_present:int;committed_new:int;exact_readback:int;observation_ids:tuple;execution_authority:bool=False
def canonicalize_verified_learned_case(e,o,acquisition_batch_id='oad188.crypto-learned-case'):
    event=assemble_learning_event(e.asset,e.evidence_hash,e.lineage_hash,o.outcome_observation)
    if not verify_learning_event(event):raise RuntimeError('invalid OCL LearningEvent')
    method=str(getattr(o,'sampling_method',''));realized=int(getattr(o,'realized_horizon_seconds',o.horizon_seconds));offset=int(getattr(o,'timing_offset_seconds',realized-int(o.horizon_seconds)));exact=bool(getattr(o,'exact_interval',False))
    if not method:raise RuntimeError('verified learned case requires certified timing sampling method')
    if offset<0 or (exact and offset!=0):raise RuntimeError('invalid learned-case timing lineage')
    payload={'experience_id':e.experience_id,'asset':e.asset,'snapshot_at':e.snapshot_at,'condition_vector':e.condition_vector,'temporal_vector':e.temporal_vector,'evidence_hash':e.evidence_hash,'condition_hash':e.condition_hash,'experience_hash':e.experience_hash,'lineage_hash':e.lineage_hash,'horizon_seconds':int(o.horizon_seconds),'requested_horizon_seconds':int(o.horizon_seconds),'realized_horizon_seconds':realized,'timing_offset_seconds':offset,'sampling_method':method,'timing_schema_version':'OAD-212','timing_certified':True,'matures_at':o.matures_at,'outcome_observed_at':o.candle_start,'start_price':o.start_price,'outcome_price':o.outcome_price,'return_fraction':o.return_fraction,'return_percent':o.return_percent,'outcome_hash':o.outcome_observation.outcome_hash,'learning_event_id':event.event_id,'learning_event_hash':event.event_hash,'outcome_type':event.outcome_type,'exact_interval':exact,'probability':None,'direction':None}
    raw=RawSourceObservation.create(source_observation_id=f'{e.experience_id}:{event.event_hash}',observed_at=datetime.fromisoformat(str(o.candle_start).replace('Z','+00:00')),observation_type='crypto_verified_learned_case',payload=payload,provenance={'producer':PRODUCER,'source_ref':o.source_ref,'source_hash':o.source_hash,'read_only':True,'timing_certified':True})
    return CanonicalObservation.create(source_id=f'{SOURCE_PREFIX}{str(e.asset).lower()}',raw_observation=raw,acquired_at=datetime.now(timezone.utc),acquisition_batch_id=acquisition_batch_id)
def persist_verified_learned_cases(pairs,root=None,timeout_seconds=120.0):
    root=Path(root or Path.cwd()).resolve();canonical=tuple(canonicalize_verified_learned_case(e,o) for e,o in tuple(pairs));backend=_backend(root);missing=[];existing=0
    for i,x in enumerate(canonical):
        if _query_one(backend,x.observation_id,i) is None:missing.append(x)
        else:existing+=1
    committed=0
    if missing:
        sub=submit_observation_batch(PRODUCER,PRIORITY,tuple(missing),root);ev=tuple(await_request(str(sub.request_id),root,float(timeout_seconds)));accepted=tuple(x for x in ev if getattr(x,'accepted',False) is True)
        if len(accepted)!=len(missing):raise RuntimeError('learned-case single-writer commit mismatch')
        committed=len(accepted)
    ids=tuple(x.observation_id for x in canonical);rows=tuple(exact_postgresql_readback(ids,root)) if ids else ()
    if len(rows)!=len(ids):raise RuntimeError('learned-case exact readback mismatch')
    return LearnedCasePersistence(len(ids),existing,committed,len(rows),ids,False)
