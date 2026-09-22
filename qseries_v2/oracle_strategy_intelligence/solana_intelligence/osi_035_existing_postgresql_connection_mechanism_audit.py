from __future__ import annotations
import ast,json,re
from pathlib import Path

AUDIT="runtime_state/solana_opportunities/postgresql_boundary_audit.json"
FOCUS=(
 "qseries_v2/ops/historical_data_store.py",
 "qseries_v2/oracle_core",
 "qseries_v2/oracle_runtime",
 "qseries_v2/oracle_adapters",
)

PATTERNS=(
 "psycopg.connect","psycopg2.connect","create_engine(","connect(",
 "DATABASE_URL","POSTGRES","PGHOST","PGPORT","PGDATABASE","PGUSER","PGPASSWORD",
 "dsn","database_url","config","dotenv","load_dotenv","os.environ","os.getenv",
)

def _inspect(path:Path,root:Path)->dict:
 text=path.read_text(encoding="utf-8",errors="replace")
 matches=[]
 for n,line in enumerate(text.splitlines(),1):
  low=line.lower()
  if any(p.lower() in low for p in PATTERNS):
   matches.append({"line":n,"text":line[:900]})
 funcs=[]
 try:
  tree=ast.parse(text)
  for node in ast.walk(tree):
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
    name=node.name.lower()
    if any(k in name for k in ("connect","postgres","database","db","store","reader","read")):
     funcs.append({"name":node.name,"line":node.lineno})
 except Exception:
  pass
 return {"module":str(path.relative_to(root)),"matches":matches[:300],"candidate_functions":funcs[:100]}

def audit(root:Path)->dict:
 ap=root/AUDIT
 if not ap.is_file():raise RuntimeError("Missing OSI-034 PostgreSQL audit")
 raw=json.loads(ap.read_text(encoding="utf-8"))
 modules=[]
 seen=set()
 for item in raw.get("postgres_modules",[]):
  rel=item.get("module","").replace("\\","/")
  p=root/rel
  if not p.is_file():continue
  pri=0 if rel=="qseries_v2/ops/historical_data_store.py" else 1
  modules.append((pri,rel,p))
 modules.sort(key=lambda x:(x[0],x[1]))
 inspected=[]
 for _,rel,p in modules[:120]:
  d=_inspect(p,root)
  if d["matches"] or d["candidate_functions"]:inspected.append(d)
 env_names=set()
 config_files=set()
 for d in inspected:
  for m in d["matches"]:
   t=m["text"]
   for name in re.findall(r'["\']([A-Z][A-Z0-9_]{3,})["\']',t):
    if any(k in name for k in ("PG","POSTGRES","DATABASE","DB_")):env_names.add(name)
   for cfg in re.findall(r'["\']([^"\']+\.(?:env|json|toml|yaml|yml|ini))["\']',t,re.I):
    config_files.add(cfg)
 return {"revision":"OSI_035C","inspected_modules":inspected,
  "environment_names":sorted(env_names),"config_file_literals":sorted(config_files),
  "execution_authority":False,"read_only":True,
  "purpose":"Find the exact existing Oracle PostgreSQL connection mechanism without inventing credentials."}

def write(root:Path)->Path:
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/postgresql_connection_mechanism_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
