from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .ocr_002_live_observation_read_model import load_env,quote_sql_identifier

OCR_012_BUILD_ID="OCR-012"
OCR_012_REVISION="OCR_012_INCREMENTAL_NEW_OBSERVATION_SELECTION_V1"
ORDER_CANDIDATES=("sequence_number","persisted_at","created_at","observed_at","acquired_at")

@dataclass(frozen=True)
class IncrementalObservationSlice:
    schema:str
    table:str
    order_column:str
    rows:tuple[dict,...]
    read_only:bool=True

def _connect(url):
    try:
        import psycopg
        return psycopg.connect(url)
    except ImportError:
        import psycopg2
        return psycopg2.connect(url)

def _discover_source(cur):
    cur.execute("""SELECT table_schema,table_name FROM information_schema.columns
                   WHERE column_name='observation_id' AND table_schema NOT IN ('pg_catalog','information_schema')
                   ORDER BY CASE WHEN table_name='oracle_canonical_observations' THEN 0
                                 WHEN table_name ILIKE '%canonical%' THEN 1
                                 WHEN table_name ILIKE '%observation%' THEN 2 ELSE 3 END,
                            table_schema,table_name LIMIT 20""")
    candidates=cur.fetchall()
    for schema,table in candidates:
        cur.execute("""SELECT column_name FROM information_schema.columns
                       WHERE table_schema=%s AND table_name=%s""",(schema,table))
        cols={r[0] for r in cur.fetchall()}
        order=next((x for x in ORDER_CANDIDATES if x in cols),None)
        if order:
            return schema,table,order
    raise RuntimeError("No observation table with a supported deterministic order column found")

def build_incremental_cursor_predicate(order_column):
    if order_column=="sequence_number":
        return "numeric"
    if order_column in ("persisted_at","created_at","observed_at","acquired_at"):
        return "timestamp"
    raise ValueError("unsupported order column")

def read_new_canonical_observations(root=None,cursor=None,limit=50):
    from .ocr_011_reasoning_cursor_state import empty_reasoning_cursor
    root=Path(root or Path.cwd()).resolve()
    cursor=cursor or empty_reasoning_cursor()
    limit=max(1,min(int(limit),500))
    env=load_env(root)
    url=env.get("DATABASE_URL") or env.get("ORACLE_DATABASE_URL")
    if not url:raise RuntimeError("DATABASE_URL not configured")
    conn=_connect(url)
    try:
        try:conn.set_session(readonly=True,autocommit=False)
        except Exception:pass
        cur=conn.cursor()
        schema,table,order=_discover_source(cur)
        if cursor.order_column and cursor.order_column!=order:
            raise RuntimeError("Reasoning cursor order column no longer matches production table")
        qschema=quote_sql_identifier(schema);qtable=quote_sql_identifier(table);qorder=quote_sql_identifier(order)
        sql=f"SELECT to_jsonb(t) FROM {qschema}.{qtable} t"
        params=[]
        if cursor.order_value:
            if order=="sequence_number":
                sql+=f" WHERE ({qorder} > %s::bigint OR ({qorder} = %s::bigint AND observation_id::text > %s))"
            else:
                sql+=f" WHERE ({qorder} > %s::timestamptz OR ({qorder} = %s::timestamptz AND observation_id::text > %s))"
            params.extend((cursor.order_value,cursor.order_value,cursor.observation_id))
        sql+=f" ORDER BY {qorder} ASC, observation_id ASC LIMIT %s"
        params.append(limit)
        cur.execute(sql,tuple(params))
        rows=tuple(dict(r[0]) for r in cur.fetchall())
        conn.rollback()
        return IncrementalObservationSlice(schema,table,order,rows,True)
    finally:
        conn.close()

def cursor_values_from_last_row(slice_):
    if not slice_.rows:raise ValueError("slice rows required")
    row=slice_.rows[-1]
    value=row.get(slice_.order_column)
    oid=row.get("observation_id")
    if value is None or oid is None:raise RuntimeError("cursor columns missing from row")
    return slice_.order_column,str(value),str(oid)

def verify_ocr_012_incremental_new_observation_selection():
    return (
        ORDER_CANDIDATES[0]=="sequence_number"
        and build_incremental_cursor_predicate("sequence_number")=="numeric"
        and build_incremental_cursor_predicate("persisted_at")=="timestamp"
        and IncrementalObservationSlice("s","t","sequence_number",tuple()).read_only
    )
