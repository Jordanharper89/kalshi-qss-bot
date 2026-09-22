from __future__ import annotations
import json,os
from pathlib import Path

AUDIT="runtime_state/solana_opportunities/postgresql_boundary_audit.json"

def _connect():
    try:
        import psycopg
    except Exception as e:
        return None,"PSYCOPG_UNAVAILABLE:"+repr(e)
    dsn=(os.environ.get("DATABASE_URL")
         or os.environ.get("POSTGRES_DSN")
         or os.environ.get("ORACLE_POSTGRES_DSN"))
    if not dsn:
        return None,"POSTGRES_DSN_NOT_FOUND"
    try:
        conn=psycopg.connect(dsn,connect_timeout=3)
        conn.autocommit=True
        return conn,None
    except Exception as e:
        return None,"CONNECT_FAILED:"+repr(e)

def inspect(root:Path,table_limit:int=100)->dict:
    ap=root/AUDIT
    if not ap.is_file():
        raise RuntimeError("Missing OSI-034 audit")
    conn,error=_connect()
    if conn is None:
        return {"connected":False,"error":error,"tables":[],
                "execution_authority":False,"read_only":True}
    try:
        with conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on")
            sql=(
                "SELECT table_schema, table_name "
                "FROM information_schema.tables "
                "WHERE table_type='BASE TABLE' "
                "AND table_schema NOT IN ('pg_catalog','information_schema') "
                "ORDER BY table_schema, table_name "
                "LIMIT %s"
            )
            cur.execute(sql,(table_limit,))
            tables=[{"schema":r[0],"table":r[1]} for r in cur.fetchall()]
        return {"connected":True,"error":None,"tables":tables,
                "execution_authority":False,"read_only":True}
    finally:
        conn.close()

def write(root:Path)->Path:
    d=inspect(root)
    p=root/"runtime_state/solana_opportunities/postgresql_read_boundary.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
    return p
