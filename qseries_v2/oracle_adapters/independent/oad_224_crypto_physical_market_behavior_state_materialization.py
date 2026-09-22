from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_continuous_learner.ocl_011_market_behavior_observation import build_market_behavior_observation,verify_market_behavior_observation
from qseries_v2.oracle_continuous_learner.ocl_012_market_behavior_learning import learn_market_behavior,verify_ocl_012_market_behavior_learning_engine
from .oad_218_existing_ocl_state_hash_envelope import envelope
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
SOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")
@dataclass(frozen=True,slots=True)
class PhysicalMarketBehaviorMaterialization:
    learned_cases:int
    behavior_observations:int
    behavior_states:tuple
    market_behavior_state_hash:str|None
    state:str
    physical_ready:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False
def materialize_physical_market_behavior_state(root=None,limit=1536):
    if not verify_ocl_012_market_behavior_learning_engine():
        raise RuntimeError("Frozen OCL-012 verifier failed")
    root=Path(root or Path.cwd()).resolve()
    sql="""SELECT observed_at,COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb)
           FROM public.oracle_canonical_observations
           WHERE source_id = ANY(%s::text[]) AND observation_type='crypto_verified_learned_case'
           ORDER BY sequence_number DESC LIMIT %s"""
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='10000ms'")
            q.execute(sql,(list(SOURCE_IDS),int(limit)));rows=q.fetchall() or []
        c.rollback()
    groups={};obs=[]
    for observed,praw in rows:
        p=praw if isinstance(praw,dict) else dict(praw or ())
        asset=str(p.get("asset") or "").upper();evh=str(p.get("evidence_hash") or "");outh=str(p.get("outcome_hash") or "")
        if not asset or len(evh)!=64 or len(outh)!=64 or p.get("return_fraction") is None: continue
        observed_at=observed.isoformat() if hasattr(observed,"isoformat") else str(p.get("outcome_observed_at") or observed)
        o=build_market_behavior_observation(asset,"crypto_realized_return","return_fraction_observed_interval",float(p["return_fraction"]),observed_at,evh,outh)
        if not verify_market_behavior_observation(o):raise RuntimeError("OCL-011 verification failed")
        obs.append(o);groups.setdefault(asset,[]).append(o)
    if not obs:
        return PhysicalMarketBehaviorMaterialization(len(rows),0,(),None,"HOLD_OUTCOME_GROUNDED_BEHAVIOR_ROWS_REQUIRED")
    states=tuple(learn_market_behavior(tuple(groups[a])) for a in sorted(groups))
    return PhysicalMarketBehaviorMaterialization(len(rows),len(obs),states,envelope("market_behavior",states).state_hash,"MATERIALIZED")
