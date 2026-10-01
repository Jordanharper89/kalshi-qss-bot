import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_040_readonly_postgresql_schema_profiler import profile,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=profile(ROOT);p=write(ROOT)
  self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"]);self.assertTrue(d["read_only"])
  print("[CONNECTED]",d["connected"])
  print("[DSN_ENV]",d.get("dsn_env"))
  print("[LOADED_ENV_NAMES]",json.dumps(d.get("loaded_env_names",[])))
  print("[ERROR]",d.get("error"))
  print("[TABLES]",len(d["tables"]))
  if d["tables"]:
   print("[TOP_TABLE]",json.dumps(d["tables"][0],sort_keys=True)[:1500])
  if not d["connected"]:
   self.fail("POSTGRESQL_READONLY_CONNECTION_FAILED")
  print("[PASS] OSI-040B read-only PostgreSQL schema profiler")
  print("[TRADER] Solana runtime reuses the repo's existing PostgreSQL credential without exposing it")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
