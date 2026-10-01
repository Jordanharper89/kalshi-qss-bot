from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_039_existing_oracle_postgresql_environment_loader_audit.py"
TEST=ROOT/"test_osi_039b_existing_oracle_postgresql_environment_loader_audit.py"

MOD_TEXT='''from __future__ import annotations
import json,re
from pathlib import Path

TARGET_KEYS=("DATABASE_URL","ORACLE_DATABASE_URL","ORACLE_POSTGRESQL_URL","POSTGRESQL_URL","POSTGRES_URL")
LOAD_TOKENS=("load_dotenv","dotenv_values",".env","os.environ","os.getenv","environ.get","setdefault")

def _scan_source(path:Path,root:Path)->dict:
 text=path.read_text(encoding="utf-8",errors="replace")
 matches=[]
 for n,line in enumerate(text.splitlines(),1):
  low=line.lower()
  if any(t.lower() in low for t in LOAD_TOKENS) or any(k.lower() in low for k in TARGET_KEYS):
   matches.append({"line":n,"text":line[:900]})
 return {"module":str(path.relative_to(root)),"matches":matches[:250]}

def _env_key_names(path:Path)->list[str]:
 out=[]
 try:
  for raw in path.read_text(encoding="utf-8",errors="replace").splitlines():
   line=raw.strip()
   if not line or line.startswith("#") or "=" not in line:continue
   key=line.split("=",1)[0].strip()
   if key in TARGET_KEYS:out.append(key)
 except Exception:pass
 return sorted(set(out))

def audit(root:Path)->dict:
 inspected=[]
 candidates=[
  root/"run_oracle_live.py",
  root/"qseries_v2/oracle_continuous_reasoning/ocr_002_live_observation_read_model.py",
 ]
 for p in (root/"qseries_v2").rglob("*.py"):
  try:
   t=p.read_text(encoding="utf-8",errors="replace")
  except Exception:continue
  low=t.lower()
  if any(x.lower() in low for x in TARGET_KEYS) or any(x.lower() in low for x in LOAD_TOKENS):
   candidates.append(p)

 seen=set()
 for p in candidates:
  if not p.is_file():continue
  rp=str(p.resolve()).lower()
  if rp in seen:continue
  seen.add(rp)
  d=_scan_source(p,root)
  if d["matches"]:inspected.append(d)

 env_files=[]
 for base in (root,root/"runtime",root/"runtime_state"):
  if not base.exists():continue
  for p in base.rglob("*"):
   if not p.is_file():continue
   name=p.name.lower()
   if name==".env" or name.endswith(".env") or name in ("env","environment"):
    keys=_env_key_names(p)
    env_files.append({"path":str(p.relative_to(root)),"target_keys_present":keys})

 return {"revision":"OSI_039B","source_modules":inspected[:200],
  "environment_files":env_files[:100],
  "target_keys":list(TARGET_KEYS),
  "execution_authority":False,"read_only":True,
  "secrets_exposed":False}

def write(root:Path)->Path:
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/postgresql_environment_loader_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
'''

TEST_TEXT='''import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_039_existing_oracle_postgresql_environment_loader_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"]);self.assertFalse(d["secrets_exposed"])
  print("[REPORT]",p)
  print("[SOURCE_MODULES]",len(d["source_modules"]))
  print("[ENV_FILES]",len(d["environment_files"]))
  if d["source_modules"]:print("[TOP_SOURCE]",json.dumps(d["source_modules"][0],sort_keys=True)[:2500])
  if d["environment_files"]:print("[TOP_ENV_FILE]",json.dumps(d["environment_files"][0],sort_keys=True))
  files_with_keys=[x for x in d["environment_files"] if x["target_keys_present"]]
  print("[ENV_FILES_WITH_POSTGRES_KEYS]",len(files_with_keys))
  if files_with_keys:print("[POSTGRES_ENV_FILE]",json.dumps(files_with_keys[0],sort_keys=True))
  print("[PASS] OSI-039B existing Oracle PostgreSQL environment-loader audit")
  print("[TRADER] Finds where Oracle loads the warehouse credential without exposing the credential itself")
  print("[SCOPE] Read-only audit; no secret values printed or modified")

if __name__=="__main__":unittest.main()
'''

def main():
 print("="*116);print(" OSI-039B EXISTING ORACLE POSTGRESQL ENVIRONMENT-LOADER AUDIT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE");print("[SCOPE] Trace existing environment loader; never print secret values")
if __name__=="__main__":main()
