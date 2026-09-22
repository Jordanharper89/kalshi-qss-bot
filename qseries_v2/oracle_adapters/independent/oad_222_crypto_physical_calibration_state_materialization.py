from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_continuous_learner.ocl_006_calibration_learning import verify_ocl_006_probability_calibration_learning
READ_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;EXECUTION_AUTHORITY=False
SOURCE_IDS=("source.crypto.learned_case.btc","source.crypto.learned_case.eth","source.crypto.learned_case.sol")
@dataclass(frozen=True,slots=True)
class PhysicalCalibrationMaterialization:
    learned_cases:int
    cases_with_historical_forecast_probability:int
    calibration_observations:int
    calibration_state_hash:str|None
    state:str
    physical_ready:bool=True
    probability_enabled:bool=False
    direction_enabled:bool=False
    execution_authority:bool=False
def materialize_physical_calibration_state(root=None,limit=1536):
    if not verify_ocl_006_probability_calibration_learning():
        raise RuntimeError("Frozen OCL-006 verifier failed")
    root=Path(root or Path.cwd()).resolve()
    sql="""SELECT COALESCE(canonical_observation_json->'raw_observation'->'payload',canonical_observation_json->'payload','{}'::jsonb)
           FROM public.oracle_canonical_observations
           WHERE source_id = ANY(%s::text[]) AND observation_type='crypto_verified_learned_case'
           ORDER BY sequence_number DESC LIMIT %s"""
    with connect(root,autocommit=False) as c:
        with c.cursor() as q:
            q.execute("SET TRANSACTION READ ONLY")
            q.execute("SET LOCAL statement_timeout='10000ms'")
            q.execute(sql,(list(SOURCE_IDS),int(limit)))
            rows=q.fetchall() or []
        c.rollback()
    payloads=[r[0] if isinstance(r[0],dict) else dict(r[0] or ()) for r in rows]
    with_probability=[p for p in payloads if p.get("probability") is not None]
    if not with_probability:
        return PhysicalCalibrationMaterialization(len(payloads),0,0,None,"HOLD_HISTORICAL_FORECAST_PROBABILITY_REQUIRED")
    return PhysicalCalibrationMaterialization(len(payloads),len(with_probability),0,None,"HOLD_VERIFIED_FORECAST_EVENT_RECONSTRUCTION_REQUIRED")
