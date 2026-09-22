from __future__ import annotations
import json,os
from pathlib import Path

ENV=("ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL","DATABASE_URL")

def _dsn(root:Path):
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

def audit(root:Path,limit:int=250)->dict:
 env_name,dsn=_dsn(root)
 if not dsn:raise RuntimeError("Existing Oracle PostgreSQL DSN unavailable")
 import psycopg
 with psycopg.connect(dsn,connect_timeout=5) as conn:
  with conn.cursor() as cur:
   cur.execute("SET TRANSACTION READ ONLY")
   cur.execute(
    "SELECT source_id, observation_type, COUNT(*) AS n, "
    "MIN(observed_at), MAX(observed_at) "
    "FROM public.oracle_canonical_observations "
    "GROUP BY source_id, observation_type "
    "ORDER BY n DESC LIMIT %s",(limit,))
   rows=cur.fetchall()
 result=[]
 for source_id,observation_type,n,first_at,last_at in rows:
  text=f"{source_id} {observation_type}".lower()
  relevant=any(k in text for k in ("solana","gmgn","pump","raydium","jupiter","orca","meteora","dex","wallet","mint","pool","swap"))
  result.append({
   "source_id":source_id,"observation_type":observation_type,"count":int(n),
   "first_observed_at":first_at.isoformat() if hasattr(first_at,"isoformat") else str(first_at),
   "last_observed_at":last_at.isoformat() if hasattr(last_at,"isoformat") else str(last_at),
   "solana_relevant":relevant})
 relevant=[x for x in result if x["solana_relevant"]]
 return {"revision":"OSI_044","dsn_env":env_name,"groups":result,
  "solana_relevant_groups":relevant,"solana_relevant_group_count":len(relevant),
  "execution_authority":False,"read_only":True}

def write(root:Path)->Path:
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/postgresql_solana_source_distribution.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
