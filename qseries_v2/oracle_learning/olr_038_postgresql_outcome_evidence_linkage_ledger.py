from __future__ import annotations
from pathlib import Path
from .olr_036_outcome_evidence_linkage_foundation import deterministic_linkage_id,build_outcome_evidence_key
OLR_038_BUILD_ID="OLR-038"
OLR_038_REVISION="OLR_038_POSTGRESQL_OUTCOME_EVIDENCE_LINKAGE_LEDGER_V1"
TABLE="oracle_outcome_evidence_linkage"

def _db():
    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
    return connect

def ensure_linkage_schema(root=None):
    ddl=f"""CREATE TABLE IF NOT EXISTS public.{TABLE}(
      linkage_id TEXT PRIMARY KEY,
      market_id TEXT NOT NULL,
      ticker TEXT NOT NULL,
      observation_id TEXT,
      matched BOOLEAN NOT NULL,
      match_method TEXT NOT NULL,
      match_score INTEGER NOT NULL,
      recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
    );
    CREATE INDEX IF NOT EXISTS oracle_outcome_evidence_linkage_market_idx
      ON public.{TABLE}(market_id,recorded_at);"""
    with _db()(root,autocommit=True) as conn:
        with conn.cursor() as cur:cur.execute(ddl)
    return True

def record_linkage(outcome,match,root=None):
    ensure_linkage_schema(root);key=build_outcome_evidence_key(outcome);lid=deterministic_linkage_id(key)
    obs=None
    if match.candidate is not None:
        obs=match.candidate.get("observation_id") if hasattr(match.candidate,"get") else getattr(match.candidate,"observation_id",None)
    with _db()(root) as conn:
        with conn.cursor() as cur:
            cur.execute(f"""INSERT INTO public.{TABLE}
              (linkage_id,market_id,ticker,observation_id,matched,match_method,match_score)
              VALUES(%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT(linkage_id) DO UPDATE SET
              observation_id=EXCLUDED.observation_id,matched=EXCLUDED.matched,
              match_method=EXCLUDED.match_method,match_score=EXCLUDED.match_score""",
              (lid,key.market_id,key.ticker,obs,bool(match.matched),str(match.method),int(match.score)))
        conn.commit()
    return lid

def verify_olr_038_postgresql_outcome_evidence_linkage_ledger(root=None):
    from .olr_037_market_evidence_candidate_matching import verify_olr_037_market_evidence_candidate_matching
    return verify_olr_037_market_evidence_candidate_matching(root) and TABLE=="oracle_outcome_evidence_linkage"
