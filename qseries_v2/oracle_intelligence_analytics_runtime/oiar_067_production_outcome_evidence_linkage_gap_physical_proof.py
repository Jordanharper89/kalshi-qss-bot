from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path

from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
from qseries_v2.oracle_production_learning import opl_001_production_learning_foundation as foundation
from qseries_v2.oracle_production_learning import opl_002_canonical_evidence_index as evidence_index

BUILD_ID="OIAR-067"
REVISION="OIAR_067_PRODUCTION_OUTCOME_EVIDENCE_LINKAGE_GAP_PHYSICAL_PROOF_V1"

@dataclass(frozen=True)
class LinkageGapProof:
    sampled_missing_settlements:int
    exact_ticker_evidence_found:int
    exact_ticker_pre_settlement_found:int
    exact_ticker_only_post_settlement:int
    exact_ticker_no_evidence:int
    evidence_rows_examined:int
    candidate_pre_settlement_rows:int
    distinct_tickers_with_pre_settlement_evidence:int
    sample_examples:tuple
    read_only:bool
    repaired_rows:int
    probability_enabled:bool
    execution_authority:bool

def _iso(v):
    return "" if v is None else (v.isoformat() if hasattr(v,"isoformat") else str(v))

def prove_linkage_gap(root=None,sample_size=100):
    root=Path(root or Path.cwd()).resolve()
    n=max(1,min(int(sample_size),500))
    with connect(root,autocommit=False) as conn:
        cur=conn.cursor()
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute("SET LOCAL statement_timeout='30000ms'")

        cur.execute(f"""
            SELECT settlement_hash,ticker,result,settlement_ts
            FROM public.{foundation.LEDGER_TABLE}
            WHERE status='EVIDENCE_MISSING'
            ORDER BY updated_at DESC, settlement_ts DESC
            LIMIT %s
        """,(n,))
        missing=cur.fetchall()

        found=pre=post_only=noev=examined=pre_rows=0
        pre_tickers=set()
        examples=[]

        sql=f"""
            SELECT observation_id,evidence_hash,sequence_number,observed_at,observation_type
            FROM public.{evidence_index.INDEX_TABLE}
            WHERE ticker=%s
            ORDER BY sequence_number DESC
            LIMIT 200
        """

        for settlement_hash,ticker,result,settlement_ts in missing:
            cur.execute(sql,(ticker,))
            rows=cur.fetchall()
            examined+=len(rows)
            if rows:
                found+=1
            before=[r for r in rows if r[3] is not None and settlement_ts is not None and r[3] < settlement_ts]
            after=[r for r in rows if r[3] is not None and settlement_ts is not None and r[3] >= settlement_ts]
            if before:
                pre+=1
                pre_rows+=len(before)
                pre_tickers.add(str(ticker))
                cls="PRE_SETTLEMENT_EVIDENCE_EXISTS"
            elif rows and after:
                post_only+=1
                cls="ONLY_POST_SETTLEMENT_EVIDENCE"
            else:
                noev+=1
                cls="NO_EXACT_TICKER_EVIDENCE"
            if len(examples)<20:
                newest_pre=max(before,key=lambda r:r[2]) if before else None
                examples.append({
                    "ticker":str(ticker),
                    "result":str(result),
                    "settlement_ts":_iso(settlement_ts),
                    "classification":cls,
                    "evidence_rows":len(rows),
                    "pre_settlement_rows":len(before),
                    "post_settlement_rows":len(after),
                    "newest_pre_sequence":None if newest_pre is None else int(newest_pre[2]),
                    "newest_pre_observed_at":"" if newest_pre is None else _iso(newest_pre[3]),
                    "newest_pre_observation_type":"" if newest_pre is None else str(newest_pre[4]),
                    "settlement_hash":str(settlement_hash),
                })

        conn.rollback()

    return LinkageGapProof(
        sampled_missing_settlements=len(missing),
        exact_ticker_evidence_found=found,
        exact_ticker_pre_settlement_found=pre,
        exact_ticker_only_post_settlement=post_only,
        exact_ticker_no_evidence=noev,
        evidence_rows_examined=examined,
        candidate_pre_settlement_rows=pre_rows,
        distinct_tickers_with_pre_settlement_evidence=len(pre_tickers),
        sample_examples=tuple(examples),
        read_only=True,
        repaired_rows=0,
        probability_enabled=False,
        execution_authority=False,
    )

def physical_probe(root=None,sample_size=100):
    return asdict(prove_linkage_gap(root,sample_size))

def verify_oiar_067_production_outcome_evidence_linkage_gap_physical_proof():
    return (
        BUILD_ID=="OIAR-067"
        and foundation.LEDGER_TABLE=="oracle_production_learning_ledger"
        and evidence_index.INDEX_TABLE=="oracle_production_learning_evidence_index"
    )
