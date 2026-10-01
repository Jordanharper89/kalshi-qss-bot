from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_035_existing_postgresql_connection_mechanism_audit.py"
TEST=ROOT/"test_osi_035c_existing_postgresql_connection_mechanism_audit.py"

MOD_TEXT='''from __future__ import annotations
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
  rel=item.get("module","").replace("\\\\","/")
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
   for name in re.findall(r'["\\\']([A-Z][A-Z0-9_]{3,})["\\\']',t):
    if any(k in name for k in ("PG","POSTGRES","DATABASE","DB_")):env_names.add(name)
   for cfg in re.findall(r'["\\\']([^"\\\']+\\.(?:env|json|toml|yaml|yml|ini))["\\\']',t,re.I):
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
'''

TEST_TEXT='''import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_035_existing_postgresql_connection_mechanism_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[REPORT]",p)
  print("[INSPECTED_MODULES]",len(d["inspected_modules"]))
  print("[ENVIRONMENT_NAMES]",json.dumps(d["environment_names"]))
  print("[CONFIG_FILE_LITERALS]",json.dumps(d["config_file_literals"]))
  if d["inspected_modules"]:
   top=d["inspected_modules"][0]
   print("[TOP_MODULE]",top["module"])
   print("[TOP_FUNCTIONS]",json.dumps(top["candidate_functions"][:20],sort_keys=True))
   print("[TOP_MATCHES]",json.dumps(top["matches"][:12],sort_keys=True))
  if not d["inspected_modules"]:self.fail("NO_EXISTING_POSTGRESQL_CONNECTION_MECHANISM_FOUND")
  print("[PASS] OSI-035C existing PostgreSQL connection mechanism audit")
  print("[TRADER] Identifies Oracle's real warehouse connection path instead of guessing a DSN")
  print("[SCOPE] Read-only source audit; no credentials printed and no database mutation")

if __name__=="__main__":unittest.main()
'''

def main():
 print("="*116);print(" OSI-035C EXISTING POSTGRESQL CONNECTION MECHANISM AUDIT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Trace existing Oracle PostgreSQL connection mechanism; do not invent credentials")
if __name__=="__main__":main()
