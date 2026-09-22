from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oph_019_postgresql_universal_ingestion_queue import connect,ensure_postgresql_ingestion_schema

OPH_030_BUILD_ID="OPH-030"
OPH_030_REVISION="OPH_030_POSTGRESQL_WRITER_RETRY_TELEMETRY_V1"
TABLE="oracle_writer_retry_telemetry"

def ensure_retry_telemetry_schema(root=None):
    ensure_postgresql_ingestion_schema(root)
    ddl=f"""
    CREATE TABLE IF NOT EXISTS public.{TABLE}(
      telemetry_id BIGSERIAL PRIMARY KEY,
      observed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
      request_id TEXT,
      producer TEXT,
      phase TEXT NOT NULL,
      category TEXT NOT NULL,
      retryable BOOLEAN NOT NULL,
      terminal BOOLEAN NOT NULL,
      attempt INTEGER NOT NULL,
      observation_count INTEGER NOT NULL,
      elapsed_ms DOUBLE PRECISION,
      error_type TEXT,
      error_message TEXT
    );
    CREATE INDEX IF NOT EXISTS oracle_writer_retry_telemetry_request_idx
      ON public.{TABLE}(request_id,observed_at);
    CREATE INDEX IF NOT EXISTS oracle_writer_retry_telemetry_category_idx
      ON public.{TABLE}(category,observed_at);
    """
    with connect(root,autocommit=True) as conn:
        with conn.cursor() as cur: cur.execute(ddl)
    return True

def record_writer_event(request_id,producer,phase,classification,attempt,observation_count,root=None,elapsed_ms=None,exc=None):
    ensure_retry_telemetry_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""INSERT INTO public.{TABLE}
                (request_id,producer,phase,category,retryable,terminal,attempt,
                 observation_count,elapsed_ms,error_type,error_message)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    str(request_id) if request_id is not None else None,
                    str(producer) if producer is not None else None,
                    str(phase),
                    str(classification.category),
                    bool(classification.retryable),
                    bool(classification.terminal),
                    int(attempt),
                    int(observation_count),
                    None if elapsed_ms is None else float(elapsed_ms),
                    None if exc is None else type(exc).__name__,
                    None if exc is None else str(exc)[:2000],
                ),
            )
        conn.commit()
    return True

def telemetry_counts(root=None):
    ensure_retry_telemetry_schema(root)
    with connect(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""SELECT category,COUNT(*) FROM public.{TABLE}
                            GROUP BY category ORDER BY category""")
            return {str(k):int(v) for k,v in cur.fetchall()}

def verify_oph_030_postgresql_writer_retry_telemetry(root=None):
    from .oph_029_postgresql_routing_failure_classification import verify_oph_029_postgresql_routing_failure_classification
    return verify_oph_029_postgresql_routing_failure_classification(root) and TABLE=="oracle_writer_retry_telemetry"
