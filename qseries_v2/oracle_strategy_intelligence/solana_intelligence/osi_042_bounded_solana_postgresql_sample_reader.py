from __future__ import annotations
import json,os,re
from pathlib import Path
ENV=("ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL","DATABASE_URL")
def _load(root:Path):
 env=root/".env"
 if env.is_file():
  try:
   from dotenv import dotenv_values
   vals=dotenv_values(env)
   for n in ENV:
    if vals.get(n) and not os.environ.get(n):os.environ[n]=str(vals[n])
  except Exception:
   for raw in env.read_text(encoding="utf-8",errors="replace").splitlines():
    if "=" not in raw or raw.lstrip().startswith("#"):continue
    k,v=raw.split("=",1);k=k.strip()
    if k in ENV and not os.environ.get(k):os.environ[k]=v.strip().strip('"').strip("'")
 for n in ENV:
  if os.environ.get(n):return n,os.environ[n]
 return None,None
def read(root:Path,limit:int=100)->dict:
 cp=root/"runtime_state/solana_opportunities/solana_postgresql_tables.json";c=json.loads(cp.read_text(encoding="utf-8"))
 candidates=[x for x in c.get("candidates",[]) if x.get("has_canonical_json")]
 if not candidates:return {"rows":[],"table":None,"row_count":0,"execution_authority":False,"read_only":True}
 table=candidates[0]["table"]
 if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*",table):raise RuntimeError("Unsafe table identifier")
 env_name,dsn=_load(root)
 if not dsn:raise RuntimeError("Existing Oracle PostgreSQL DSN unavailable after root .env load")
 import psycopg
 schema,name=table.split(".",1)
 with psycopg.connect(dsn,connect_timeout=5) as conn:
  with conn.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY")
   sql=f'SELECT observed_at,source_id,observation_type,canonical_observation_json FROM "{schema}"."{name}" ORDER BY observed_at DESC LIMIT %s'
   cur.execute(sql,(limit,));vals=cur.fetchall()
 rows=[{"observed_at":r[0].isoformat() if hasattr(r[0],"isoformat") else str(r[0]),"source_id":r[1],"observation_type":r[2],"canonical_observation_json":r[3]} for r in vals]
 return {"table":table,"dsn_env":env_name,"rows":rows,"row_count":len(rows),"execution_authority":False,"read_only":True}
