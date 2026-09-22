from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json

OPL_001_BUILD_ID="OPL-001"
OPL_001_REVISION="OPL_001_PRODUCTION_LEARNING_FOUNDATION_V1"
STATE_TABLE="oracle_production_learning_state"
LEDGER_TABLE="oracle_production_learning_ledger"

def connect(root=None,autocommit=False):
    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect as c
    return c(root,autocommit=autocommit)

def ensure_production_learning_schema(root=None):
    ddl=f"""
    CREATE TABLE IF NOT EXISTS public.{STATE_TABLE}(
      state_id INTEGER PRIMARY KEY CHECK(state_id=1),
      legacy_outcomes_learned BIGINT NOT NULL DEFAULT 0,
      production_outcomes_learned BIGINT NOT NULL DEFAULT 0,
      cycles BIGINT NOT NULL DEFAULT 0,
      applied_through_sequence BIGINT NOT NULL DEFAULT 0,
      ocl_state_json JSONB,
      last_settlement_ts TEXT NOT NULL DEFAULT '',
      last_ticker TEXT NOT NULL DEFAULT '',
      state_hash TEXT NOT NULL DEFAULT '',
      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
    );

    CREATE TABLE IF NOT EXISTS public.{LEDGER_TABLE}(
      settlement_hash TEXT PRIMARY KEY,
      ticker TEXT NOT NULL,
      result TEXT NOT NULL,
      settlement_ts TEXT NOT NULL,
      evidence_observation_id TEXT,
      evidence_hash TEXT,
      evidence_sequence_number BIGINT,
      learning_event_hash TEXT,
      status TEXT NOT NULL CHECK(status IN ('EVIDENCE_MISSING','ELIGIBLE','LEARNED','REJECTED')),
      first_seen_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      learned_at TIMESTAMPTZ
    );

    CREATE INDEX IF NOT EXISTS oracle_production_learning_ledger_ticker_idx
      ON public.{LEDGER_TABLE}(ticker,status,settlement_ts);
    """
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur:cur.execute(ddl)
    return True

def legacy_learned_count(root=None):
    root=Path(root or Path.cwd()).resolve()
    p=root/"runtime_state"/"oracle_learning_runtime_state.json"
    if not p.is_file():return 0
    try:
        return int(json.loads(p.read_text(encoding="utf-8")).get("outcomes_learned",0))
    except Exception:
        return 0

def initialize_production_learning_state(root=None):
    ensure_production_learning_schema(root)
    legacy=legacy_learned_count(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""INSERT INTO public.{STATE_TABLE}
                    (state_id,legacy_outcomes_learned)
                    VALUES(1,%s)
                    ON CONFLICT(state_id) DO NOTHING""",
                (legacy,),
            )
        conn.commit()
    return legacy

def read_production_learning_state(root=None):
    ensure_production_learning_schema(root)
    initialize_production_learning_state(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT legacy_outcomes_learned,production_outcomes_learned,
                cycles,applied_through_sequence,ocl_state_json,last_settlement_ts,
                last_ticker,state_hash
                FROM public.{STATE_TABLE} WHERE state_id=1""")
            row=cur.fetchone()
    return {
        "legacy_outcomes_learned":int(row[0]),
        "production_outcomes_learned":int(row[1]),
        "cycles":int(row[2]),
        "applied_through_sequence":int(row[3]),
        "ocl_state_json":row[4],
        "last_settlement_ts":str(row[5] or ""),
        "last_ticker":str(row[6] or ""),
        "state_hash":str(row[7] or ""),
    }

def verify_opl_001_production_learning_foundation(root=None):
    return OPL_001_BUILD_ID=="OPL-001" and STATE_TABLE.endswith("_state") and LEDGER_TABLE.endswith("_ledger")
