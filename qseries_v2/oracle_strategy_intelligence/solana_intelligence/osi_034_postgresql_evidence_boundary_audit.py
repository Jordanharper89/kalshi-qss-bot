from __future__ import annotations
import ast,json,re
from pathlib import Path

KEYS=("postgres","psycopg","sqlalchemy","information_schema","select ","insert into","create table","database_url","dsn")
def audit(root:Path)->dict:
 hits=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  try:text=p.read_text(encoding="utf-8",errors="replace")
  except Exception:continue
  low=text.lower()
  if not any(k in low for k in KEYS):continue
  lines=[]
  for n,line in enumerate(text.splitlines(),1):
   if any(k in line.lower() for k in KEYS):lines.append({"line":n,"text":line[:700]})
  hits.append({"module":str(p.relative_to(root)),"matches":lines[:250]})
 return {"revision":"OSI_034","postgres_modules":hits,"module_count":len(hits),
  "execution_authority":False,"read_only":True,
  "purpose":"Find existing PostgreSQL read/write pavement for bounded Solana evidence reads."}
def write(root:Path)->Path:
 d=audit(root);p=root/"runtime_state/solana_opportunities/postgresql_boundary_audit.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
