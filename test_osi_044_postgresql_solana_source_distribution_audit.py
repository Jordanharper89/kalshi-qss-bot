import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_044_postgresql_solana_source_distribution_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[REPORT]",p)
  print("[GROUPS]",len(d["groups"]))
  print("[SOLANA_RELEVANT_GROUPS]",d["solana_relevant_group_count"])
  if d["groups"]:print("[TOP_GROUP]",json.dumps(d["groups"][0],sort_keys=True))
  for row in d["solana_relevant_groups"][:20]:
   print("[SOLANA_GROUP]",json.dumps(row,sort_keys=True))
  if not d["solana_relevant_groups"]:
   self.fail("NO_SOLANA_OR_GMGN_SOURCE_GROUPS_IN_CANONICAL_POSTGRESQL")
  print("[PASS] OSI-044 PostgreSQL Solana source distribution audit")
  print("[TRADER] Locates the exact Solana/GMGN shelves inside Oracle's canonical warehouse")
  print("[SCOPE] Read-only aggregate audit; no row mutation")

if __name__=="__main__":
 unittest.main()
