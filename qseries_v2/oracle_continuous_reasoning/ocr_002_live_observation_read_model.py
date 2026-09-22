from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json,os,re

OCR_002_BUILD_ID="OCR-002"
OCR_002_REVISION="OCR_002_POSTGRESQL_LIVE_OBSERVATION_READ_MODEL_V1"

IDENT=re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

@dataclass(frozen=True)
class LiveObservationReadResult:
    schema:str
    table:str
    rows:tuple[dict,...]
    read_only:bool=True

def load_env(root):
    env=dict(os.environ)
    p=Path(root)/".env"
    if p.is_file():
        for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
            line=raw.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); k=k.strip(); v=v.strip().strip('"').strip("'")
            if k and k not in env: env[k]=v
    return env

def _connect(url):
    try:
        import psycopg
        return psycopg.connect(url)
    except ImportError:
        import psycopg2
        return psycopg2.connect(url)

def quote_sql_identifier(name):
    if not IDENT.fullmatch(name): raise ValueError("unsafe SQL identifier")
    return '"'+name+'"'

def read_latest_canonical_observations(root=None,limit=25):
    root=Path(root or Path.cwd()).resolve()
    limit=max(1,min(int(limit),100))
    env=load_env(root)
    url=env.get("DATABASE_URL") or env.get("ORACLE_DATABASE_URL")
    if not url: raise RuntimeError("DATABASE_URL not configured")
    conn=_connect(url)
    try:
        try: conn.set_session(readonly=True,autocommit=False)
        except Exception: pass
        cur=conn.cursor()
        cur.execute("""SELECT table_schema,table_name FROM information_schema.columns
                       WHERE column_name='observation_id' AND table_schema NOT IN ('pg_catalog','information_schema')
                       ORDER BY CASE WHEN table_name ILIKE '%canonical%' THEN 0 WHEN table_name ILIKE '%observation%' THEN 1 ELSE 2 END,
                                table_schema,table_name LIMIT 20""")
        candidates=cur.fetchall()
        if not candidates: raise RuntimeError("No PostgreSQL observation table with observation_id column found")
        last_error=None
        for schema,table in candidates:
            try:
                cur.execute("""SELECT column_name FROM information_schema.columns
                               WHERE table_schema=%s AND table_name=%s""",(schema,table))
                cols={r[0] for r in cur.fetchall()}
                order=next((c for c in ("sequence_number","persisted_at","observed_at","created_at","acquired_at") if c in cols),None)
                sql=f"SELECT to_jsonb(t) FROM {quote_sql_identifier(schema)}.{quote_sql_identifier(table)} t"
                if order: sql+=f" ORDER BY {quote_sql_identifier(order)} DESC"
                sql+=" LIMIT %s"
                cur.execute(sql,(limit,))
                rows=tuple(dict(r[0]) for r in cur.fetchall())
                if rows:
                    conn.rollback()
                    return LiveObservationReadResult(schema,table,rows,True)
            except Exception as exc:
                conn.rollback(); last_error=exc; cur=conn.cursor()
        raise RuntimeError("Observation tables found but no readable rows: "+str(last_error))
    finally:
        conn.close()

def verify_ocr_002_postgresql_live_observation_read_model():
    return quote_sql_identifier("observation_id")=='"observation_id"' and LiveObservationReadResult("s","t",tuple()).read_only
