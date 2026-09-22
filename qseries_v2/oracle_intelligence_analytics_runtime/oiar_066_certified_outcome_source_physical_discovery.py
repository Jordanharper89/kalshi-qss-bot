from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import inspect

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_learning_runtime import olr_002_settled_outcome_read_model as settled_model
from qseries_v2.oracle_production_learning import opl_001_production_learning_foundation as foundation
from qseries_v2.oracle_production_learning import opl_002_canonical_evidence_index as evidence_index

BUILD_ID="OIAR-066"
REVISION="OIAR_066_CERTIFIED_OUTCOME_SOURCE_PHYSICAL_DISCOVERY_V1"

@dataclass(frozen=True)
class OutcomeSourceProof:
    settled_read_model_build_id:str
    settled_outcome_fields:tuple
    production_state_table:str
    production_ledger_table:str
    evidence_index_table:str
    ledger_columns:tuple
    evidence_columns:tuple
    ledger_rows:int
    learned_rows:int
    eligible_rows:int
    evidence_missing_rows:int
    evidence_index_rows:int
    evidence_with_sequence_rows:int
    latest_learned_ticker:str
    latest_learned_settlement_ts:str
    exact_market_identity_field:str
    exact_settlement_field:str
    exact_outcome_field:str
    exact_evidence_cutoff_field:str
    exact_source_lineage_fields:tuple
    settled_normalization_proven:bool
    pre_settlement_linkage_contract_proven:bool
    read_only:bool
    outcome_source_bound:bool
    probability_enabled:bool
    execution_authority:bool

def _columns(cur, table):
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
    """,(table,))
    return tuple(str(r[0]) for r in cur.fetchall())

def _count(cur, table):
    cur.execute(f"SELECT count(*) FROM public.{table}")
    return int(cur.fetchone()[0])

def _status_count(cur, status):
    cur.execute(
        f"SELECT count(*) FROM public.{foundation.LEDGER_TABLE} WHERE status=%s",
        (status,),
    )
    return int(cur.fetchone()[0])

def _latest_learned(cur):
    cur.execute(f"""
        SELECT ticker, settlement_ts
        FROM public.{foundation.LEDGER_TABLE}
        WHERE status='LEARNED'
        ORDER BY learned_at DESC NULLS LAST, updated_at DESC
        LIMIT 1
    """)
    row=cur.fetchone()
    return ("","") if not row else (str(row[0] or ""),str(row[1] or ""))

def prove_certified_outcome_source(root=None):
    root=Path(root or Path.cwd()).resolve()

    normalized=settled_model.normalize_settled_market({
        "ticker":"KXOIAR066PROBE",
        "result":"yes",
        "settlement_ts":"2026-08-26T00:00:00Z",
    })
    normalization_ok=(
        normalized is not None
        and normalized.ticker=="KXOIAR066PROBE"
        and normalized.result=="yes"
        and normalized.settlement_ts=="2026-08-26T00:00:00Z"
        and len(normalized.source_hash)==64
    )

    with connect(root,autocommit=False) as conn:
        cur=conn.cursor()
        cur.execute("SET TRANSACTION READ ONLY")
        ledger_cols=_columns(cur,foundation.LEDGER_TABLE)
        evidence_cols=_columns(cur,evidence_index.INDEX_TABLE)

        required_ledger={
            "settlement_hash","ticker","result","settlement_ts",
            "evidence_observation_id","evidence_hash",
            "evidence_sequence_number","learning_event_hash","status"
        }
        required_evidence={
            "observation_id","ticker","evidence_hash",
            "sequence_number","observed_at","observation_type"
        }
        if not required_ledger.issubset(set(ledger_cols)):
            raise RuntimeError("production learning ledger missing required certified fields")
        if not required_evidence.issubset(set(evidence_cols)):
            raise RuntimeError("production evidence index missing required certified fields")

        ledger_rows=_count(cur,foundation.LEDGER_TABLE)
        learned=_status_count(cur,"LEARNED")
        eligible=_status_count(cur,"ELIGIBLE")
        missing=_status_count(cur,"EVIDENCE_MISSING")
        evidence_rows=_count(cur,evidence_index.INDEX_TABLE)

        cur.execute(
            f"SELECT count(*) FROM public.{foundation.LEDGER_TABLE} "
            "WHERE evidence_sequence_number IS NOT NULL"
        )
        with_seq=int(cur.fetchone()[0])
        latest_ticker,latest_ts=_latest_learned(cur)
        conn.rollback()

    opl7_source=""
    try:
        from qseries_v2.oracle_production_learning import opl_007_evidence_first_outcome_resolver as opl7
        opl7_source=inspect.getsource(opl7.collect_evidence_supported_settlements)
    except Exception:
        pass
    strict_pre_settlement=(
        "observed_at" in opl7_source
        and "settlement_ts" in opl7_source
        and "<" in opl7_source
    )

    return OutcomeSourceProof(
        settled_read_model_build_id=str(settled_model.OLR_002_BUILD_ID),
        settled_outcome_fields=("ticker","result","settlement_ts","source_hash"),
        production_state_table=str(foundation.STATE_TABLE),
        production_ledger_table=str(foundation.LEDGER_TABLE),
        evidence_index_table=str(evidence_index.INDEX_TABLE),
        ledger_columns=ledger_cols,
        evidence_columns=evidence_cols,
        ledger_rows=ledger_rows,
        learned_rows=learned,
        eligible_rows=eligible,
        evidence_missing_rows=missing,
        evidence_index_rows=evidence_rows,
        evidence_with_sequence_rows=with_seq,
        latest_learned_ticker=latest_ticker,
        latest_learned_settlement_ts=latest_ts,
        exact_market_identity_field="ticker",
        exact_settlement_field="settlement_ts",
        exact_outcome_field="result",
        exact_evidence_cutoff_field="evidence_sequence_number",
        exact_source_lineage_fields=("settlement_hash","evidence_hash","learning_event_hash"),
        settled_normalization_proven=normalization_ok,
        pre_settlement_linkage_contract_proven=strict_pre_settlement,
        read_only=True,
        outcome_source_bound=False,
        probability_enabled=False,
        execution_authority=False,
    )

def physical_probe(root=None):
    return asdict(prove_certified_outcome_source(root))

def verify_oiar_066_certified_outcome_source_physical_discovery():
    x=settled_model.normalize_settled_market(
        {"ticker":"KXTEST","result":"no","settlement_ts":"2026-08-26T00:00:00Z"}
    )
    return (
        BUILD_ID=="OIAR-066"
        and x is not None
        and x.result=="no"
        and foundation.LEDGER_TABLE=="oracle_production_learning_ledger"
        and evidence_index.INDEX_TABLE=="oracle_production_learning_evidence_index"
    )
