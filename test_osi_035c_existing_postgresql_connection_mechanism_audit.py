import json,unittest
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
