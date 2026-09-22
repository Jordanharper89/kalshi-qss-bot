from __future__ import annotations
import json,os,re
from pathlib import Path
ENV_NAMES=("ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL","DATABASE_URL")
def resolve(root:Path)->dict:
 found=[]
 for name in ENV_NAMES:
  if os.environ.get(name):found.append(name)
 modules=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  try:t=p.read_text(encoding="utf-8",errors="replace")
  except Exception:continue
  if "psycopg" not in t.lower() and "postgres" not in t.lower():continue
  hits=[]
  for n,line in enumerate(t.splitlines(),1):
   low=line.lower()
   if "psycopg.connect" in low or "psycopg2.connect" in low or any(x.lower() in low for x in ENV_NAMES):
    hits.append({"line":n,"text":line[:700]})
  if hits:modules.append({"module":str(p.relative_to(root)),"matches":hits[:80]})
 return {"revision":"OSI_039","present_environment_names":found,"candidate_modules":modules[:150],
  "execution_authority":False,"read_only":True}
def write(root:Path)->Path:
 d=resolve(root);p=root/"runtime_state/solana_opportunities/postgresql_connector_resolver.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
