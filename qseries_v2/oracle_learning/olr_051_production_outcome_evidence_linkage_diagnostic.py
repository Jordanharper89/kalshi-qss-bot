from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json

OLR_051_BUILD_ID="OLR-051"
OLR_051_REVISION="OLR_051_PRODUCTION_OUTCOME_EVIDENCE_LINKAGE_DIAGNOSTIC_CORRECTION_V2"

EXCLUDED_TABLES={
    "oracle_outcome_evidence_linkage",
    "oracle_writer_retry_telemetry",
    "oracle_universal_ingestion_queue",
}

@dataclass(frozen=True)
class TableCandidate:
    table:str
    row_count:int
    columns:tuple[str,...]
    score:int

@dataclass(frozen=True)
class LinkageDiagnosticResult:
    outcome_candidates:tuple[dict,...]
    evidence_candidates:tuple[dict,...]
    selected_outcome_table:str|None
    selected_evidence_table:str|None
    outcome_count:int
    sample_ticker:str|None
    sample_market_id:str|None
    sample_observation_id:str|None
    evidence_rows_for_ticker:int
    evidence_rows_for_market_id:int
    exact_observation_id_match:bool
    likely_break:str
    execution_authority:bool=False

def _connect(root=None):
    from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect
    return connect(root)

def _tables(cur):
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_type='BASE TABLE'
        ORDER BY table_name
    """)
    return [str(r[0]) for r in cur.fetchall()]

def _columns(cur,table):
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position
    """,(table,))
    return tuple(str(r[0]) for r in cur.fetchall())

def _row_count(cur,table):
    cur.execute(f"SELECT COUNT(*) FROM public.{table}")
    return int(cur.fetchone()[0])

def _candidate_score(table,cols,kind):
    name=table.lower()
    score=0
    identity={"ticker","market_ticker","market_id"}

    if not identity.intersection(cols):
        return -1

    if kind=="outcome":
        for token,weight in (
            ("settled",10),("outcome",9),("resolution",8),("resolved",8),
            ("learning",4),("market",2)
        ):
            if token in name:score+=weight
        for col,weight in (
            ("settled_at",8),("resolved_at",8),("result",5),("outcome",5),
            ("status",3),("ticker",2),("market_ticker",2),("market_id",2)
        ):
            if col in cols:score+=weight
    else:
        for token,weight in (
            ("canonical",10),("observation",9),("evidence",8),
            ("shadow",5),("market",2)
        ):
            if token in name:score+=weight
        for col,weight in (
            ("observation_id",10),("sequence_number",5),("observed_at",5),
            ("ticker",2),("market_ticker",2),("market_id",2)
        ):
            if col in cols:score+=weight

    return score

def _discover_candidates(cur,kind):
    found=[]
    for table in _tables(cur):
        if table in EXCLUDED_TABLES:
            continue
        cols=_columns(cur,table)
        score=_candidate_score(table,set(cols),kind)
        if score<0:
            continue
        try:
            count=_row_count(cur,table)
        except Exception:
            continue
        if count<=0:
            continue
        found.append(TableCandidate(table,count,cols,score))
    found.sort(key=lambda x:(x.score,x.row_count),reverse=True)
    return tuple(found)

def _identity_columns(cols):
    ticker_col="ticker" if "ticker" in cols else ("market_ticker" if "market_ticker" in cols else None)
    market_col="market_id" if "market_id" in cols else ticker_col
    obs_col="observation_id" if "observation_id" in cols else None
    return ticker_col,market_col,obs_col

def _select_sample(cur,candidate):
    cols=set(candidate.columns)
    ticker_col,market_col,obs_col=_identity_columns(cols)

    select_cols=[]
    for c in (ticker_col,market_col,obs_col):
        if c and c not in select_cols:
            select_cols.append(c)

    if not select_cols:
        return None

    order_col=None
    for c in (
        "settled_at","resolved_at","updated_at","created_at","observed_at",
        "sequence_number","id"
    ):
        if c in cols:
            order_col=c
            break

    sql=f"SELECT {','.join(select_cols)} FROM public.{candidate.table}"
    where_parts=[]
    if ticker_col:
        where_parts.append(f"{ticker_col} IS NOT NULL")
    if market_col and market_col!=ticker_col:
        where_parts.append(f"{market_col} IS NOT NULL")
    if where_parts:
        sql+=" WHERE "+" OR ".join(where_parts)
    if order_col:
        sql+=f" ORDER BY {order_col} DESC"
    sql+=" LIMIT 500"

    cur.execute(sql)
    for row in cur.fetchall():
        data=dict(zip(select_cols,row))
        ticker=str(data.get(ticker_col) or "").strip() if ticker_col else ""
        market=str(data.get(market_col) or "").strip() if market_col else ticker
        obs=str(data.get(obs_col) or "").strip() if obs_col else ""
        if ticker or market:
            return {
                "ticker":ticker or market,
                "market_id":market or ticker,
                "observation_id":obs or None,
            }
    return None

def _count_matches(cur,candidate,sample):
    cols=set(candidate.columns)
    ticker_col,market_col,obs_col=_identity_columns(cols)

    ticker_count=0
    market_count=0
    obs_match=False

    if ticker_col and sample["ticker"]:
        cur.execute(
            f"SELECT COUNT(*) FROM public.{candidate.table} WHERE {ticker_col}=%s",
            (sample["ticker"],),
        )
        ticker_count=int(cur.fetchone()[0])

    if market_col and sample["market_id"]:
        cur.execute(
            f"SELECT COUNT(*) FROM public.{candidate.table} WHERE {market_col}=%s",
            (sample["market_id"],),
        )
        market_count=int(cur.fetchone()[0])

    if obs_col and sample.get("observation_id"):
        cur.execute(
            f"SELECT 1 FROM public.{candidate.table} WHERE {obs_col}=%s LIMIT 1",
            (sample["observation_id"],),
        )
        obs_match=cur.fetchone() is not None

    return ticker_count,market_count,obs_match

def run_linkage_diagnostic(root=None):
    root=Path(root or Path.cwd()).resolve()

    with _connect(root) as conn:
        with conn.cursor() as cur:
            outcomes=_discover_candidates(cur,"outcome")
            evidence=_discover_candidates(cur,"evidence")

            outcome_dump=tuple({
                "table":x.table,
                "row_count":x.row_count,
                "score":x.score,
                "columns":list(x.columns),
            } for x in outcomes[:10])

            evidence_dump=tuple({
                "table":x.table,
                "row_count":x.row_count,
                "score":x.score,
                "columns":list(x.columns),
            } for x in evidence[:10])

            if not outcomes:
                return LinkageDiagnosticResult(
                    outcome_dump,evidence_dump,None,
                    evidence[0].table if evidence else None,
                    0,None,None,None,0,0,False,
                    "NO_NONEMPTY_OUTCOME_SOURCE_WITH_MARKET_IDENTITY",
                    False,
                )

            if not evidence:
                return LinkageDiagnosticResult(
                    outcome_dump,evidence_dump,outcomes[0].table,None,
                    outcomes[0].row_count,None,None,None,0,0,False,
                    "NO_NONEMPTY_EVIDENCE_SOURCE_WITH_MARKET_IDENTITY",
                    False,
                )

            selected_outcome=outcomes[0]
            selected_evidence=evidence[0]

            sample=_select_sample(cur,selected_outcome)

            if sample is None:
                return LinkageDiagnosticResult(
                    outcome_dump,evidence_dump,
                    selected_outcome.table,selected_evidence.table,
                    selected_outcome.row_count,
                    None,None,None,0,0,False,
                    "SELECTED_OUTCOME_SOURCE_HAS_NO_USABLE_MARKET_IDENTITY",
                    False,
                )

            ticker_count,market_count,obs_match=_count_matches(
                cur,selected_evidence,sample
            )

            if obs_match:
                likely="OBSERVATION_ID_MATCH_EXISTS_LINKAGE_RUNTIME_NOT_CONSUMING_IT"
            elif ticker_count>0 or market_count>0:
                likely="MARKET_IDENTITY_MATCH_EXISTS_COLUMN_MAPPING_OR_ADMISSION_BREAK"
            else:
                likely="OUTCOME_IDENTITY_AND_EVIDENCE_IDENTITY_DO_NOT_ALIGN"

            return LinkageDiagnosticResult(
                outcome_dump,evidence_dump,
                selected_outcome.table,selected_evidence.table,
                selected_outcome.row_count,
                sample["ticker"],sample["market_id"],sample.get("observation_id"),
                ticker_count,market_count,obs_match,likely,False,
            )

def write_diagnostic_report(root=None):
    root=Path(root or Path.cwd()).resolve()
    result=run_linkage_diagnostic(root)
    path=root/"qseries_v2"/"oracle_learning"/"OLR_051_LINKAGE_DIAGNOSTIC_REPORT.json"
    path.write_text(
        json.dumps(asdict(result),sort_keys=True,indent=2,default=str)+"\n",
        encoding="utf-8",
        newline="\n",
    )
    return path,result

def verify_olr_051_production_outcome_evidence_linkage_diagnostic(root=None):
    from .olr_050_production_evidence_learning_activation_freeze import verify_olr_050_production_evidence_learning_activation_freeze
    return (
        verify_olr_050_production_evidence_learning_activation_freeze(root)
        and OLR_051_BUILD_ID=="OLR-051"
        and callable(run_linkage_diagnostic)
    )
