import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_034_postgresql_evidence_boundary_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT);self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[REPORT]",p);print("[POSTGRES_MODULES]",d["module_count"])
  if d["postgres_modules"]:print("[TOP_MODULE]",d["postgres_modules"][0]["module"])
  if not d["postgres_modules"]:self.fail("NO_EXISTING_POSTGRESQL_PAVEMENT_FOUND")
  print("[PASS] OSI-034 PostgreSQL evidence boundary audit")
  print("[TRADER] Finds Oracle's existing historical evidence warehouse boundary instead of creating another database")
  print("[SCOPE] Read-only source audit")
if __name__=="__main__":unittest.main()
