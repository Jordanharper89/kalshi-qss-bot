import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_039_existing_oracle_postgresql_connector_resolver import resolve,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=resolve(ROOT);p=write(ROOT);self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[ENV_PRESENT]",json.dumps(d["present_environment_names"]))
  print("[CONNECTOR_MODULES]",len(d["candidate_modules"]))
  if d["candidate_modules"]:print("[TOP_CONNECTOR]",json.dumps(d["candidate_modules"][0],sort_keys=True))
  if not d["present_environment_names"]:self.fail("NO_EXISTING_ORACLE_POSTGRES_ENVIRONMENT_VARIABLE_PRESENT")
  print("[PASS] OSI-039 existing Oracle PostgreSQL connector resolver")
  print("[TRADER] Reuses Oracle's real database connection instead of inventing a second credential path")
if __name__=="__main__":unittest.main()
