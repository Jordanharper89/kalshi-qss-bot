from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_continuous_learner.ocl_007_source_reliability import verify_ocl_007_source_reliability_learning
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
SOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")
@dataclass(frozen=True,slots=True)
class PhysicalSourceReliabilityMaterialization:
    learned_cases:int
    source_correctness_labels:int
    source_states:int
    source_reliability_state_hash:str|None
    state:str
    physical_ready:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False
def materialize_physical_source_reliability_state(root=None,limit=1536):
    if not verify_ocl_007_source_reliability_learning():
        raise RuntimeError("Frozen OCL-007 verifier failed")
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
    labels=[]
    for p in payloads:
        v=p.get("source_correctness")
        if isinstance(v,dict): labels.extend(v.items())
        elif p.get("source_id") is not None and p.get("source_correct") is not None:
            labels.append((p.get("source_id"),bool(p.get("source_correct"))))
    if not labels:
        return PhysicalSourceReliabilityMaterialization(len(payloads),0,0,None,"HOLD_SOURCE_CORRECTNESS_LABELS_REQUIRED")
    return PhysicalSourceReliabilityMaterialization(len(payloads),len(labels),0,None,"HOLD_CERTIFIED_SOURCE_LABEL_PROVENANCE_REQUIRED")
