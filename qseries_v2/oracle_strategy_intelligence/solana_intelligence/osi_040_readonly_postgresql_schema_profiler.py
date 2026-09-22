from __future__ import annotations
import json,os
from pathlib import Path

ENV=("ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL","DATABASE_URL")

def _load_root_env(root:Path)->list[str]:
 loaded=[]
 env_path=root/".env"
 if not env_path.is_file():
  return loaded
 try:
  from dotenv import dotenv_values
  vals=dotenv_values(env_path)
  for name in ENV:
   value=vals.get(name)
   if value and not os.environ.get(name):
    os.environ[name]=str(value)
    loaded.append(name)
  return loaded
 except Exception:
  pass
 try:
  for raw in env_path.read_text(encoding="utf-8",errors="replace").splitlines():
   line=raw.strip()
   if not line or line.startswith("#") or "=" not in line:
    continue
   key,value=line.split("=",1)
   key=key.strip()
   if key not in ENV or os.environ.get(key):
    continue
   value=value.strip().strip('"').strip("'")
   if value:
    os.environ[key]=value
    loaded.append(key)
 except Exception:
  pass
 return loaded

def _dsn(root:Path):
 loaded=_load_root_env(root)
 for name in ENV:
  value=os.environ.get(name)
  if value:
   return name,value,loaded
 return None,None,loaded

def profile(root:Path)->dict:
 name,dsn,loaded=_dsn(root)
 if not dsn:
  return {"connected":False,"dsn_env":None,"loaded_env_names":loaded,
          "error":"NO_EXISTING_DSN_AFTER_ROOT_ENV_LOAD","tables":[],
          "execution_authority":False,"read_only":True}
 try:
  import psycopg
 except Exception as e:
  return {"connected":False,"dsn_env":name,"loaded_env_names":loaded,
          "error":"PSYCOPG:"+repr(e),"tables":[],
          "execution_authority":False,"read_only":True}
 try:
  with psycopg.connect(dsn,connect_timeout=5) as conn:
   with conn.cursor() as cur:
    cur.execute("SET TRANSACTION READ ONLY")
    sql=("SELECT table_schema,table_name,column_name,data_type "
         "FROM information_schema.columns "
         "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
         "ORDER BY table_schema,table_name,ordinal_position")
    cur.execute(sql)
    rows=cur.fetchall()
  grouped={}
  for s,t,c,d in rows:
   grouped.setdefault(f"{s}.{t}",[]).append({"column":c,"type":d})
  return {"connected":True,"dsn_env":name,"loaded_env_names":loaded,
          "error":None,
          "tables":[{"table":k,"columns":v} for k,v in grouped.items()],
          "execution_authority":False,"read_only":True}
 except Exception as e:
  return {"connected":False,"dsn_env":name,"loaded_env_names":loaded,
          "error":repr(e),"tables":[],
          "execution_authority":False,"read_only":True}

def write(root:Path)->Path:
 d=profile(root)
 p=root/"runtime_state/solana_opportunities/postgresql_schema_profile.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
