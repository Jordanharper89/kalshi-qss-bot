import json,unittest
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
