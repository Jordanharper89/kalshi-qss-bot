from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_continuous_learner.ocl_022_learning_maturity import evaluate_learning_maturity,verify_ocl_022_learning_confidence_evidence_maturity
from .oad_218_existing_ocl_state_hash_envelope import envelope
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
SOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")
@dataclass(frozen=True,slots=True)
class PhysicalMaturityMaterialization:
    evidence_count:int
    independent_sources:int
    consistency:float
    contradiction_rate:float
    calibration_quality:float
    maturity:object
    maturity_state_hash:str
    state:str
    physical_ready:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False
def materialize_physical_maturity_state(root=None,limit=1536):
    if not verify_ocl_022_learning_confidence_evidence_maturity():
        raise RuntimeError("Frozen OCL-022 verifier failed")
    root=Path(root or Path.cwd()).resolve()
    sql="""SELECT COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb)
           FROM public.oracle_canonical_observations
           WHERE source_id = ANY(%s::text[]) AND observation_type='crypto_verified_learned_case'
           ORDER BY sequence_number DESC LIMIT %s"""
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout='10000ms'")
            q.execute(sql,(list(SOURCE_IDS),int(limit)));rows=q.fetchall() or []
        c.rollback()
    payloads=[r[0] if isinstance(r[0],dict) else dict(r[0] or ()) for r in rows]
    returns=[float(p["return_fraction"]) for p in payloads if p.get("return_fraction") is not None]
    if returns:
        pos=sum(x>0 for x in returns);neg=sum(x<0 for x in returns);flat=len(returns)-pos-neg
        consistency=max(pos,neg,flat)/len(returns);contradiction=min(pos,neg)/len(returns)
    else:
        consistency=0.0;contradiction=0.0
    source_families=set()
    for p in payloads:
        for row in tuple(p.get("condition_vector") or ()):
            if isinstance(row,(list,tuple)) and row:source_families.add(str(row[0]))
    calibration_quality=0.0
    maturity=evaluate_learning_maturity(len(returns),len(source_families),consistency,contradiction,calibration_quality)
    return PhysicalMaturityMaterialization(len(returns),len(source_families),consistency,contradiction,calibration_quality,maturity,envelope("maturity",maturity).state_hash,"MATERIALIZED_UNCALIBRATED")
