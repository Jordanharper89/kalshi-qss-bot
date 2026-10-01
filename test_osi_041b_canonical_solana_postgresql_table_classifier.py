import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_041_solana_relevant_postgresql_table_classifier import classify,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=classify(ROOT);p=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[CANDIDATE_TABLES]",d["candidate_count"])
  if d["candidates"]:print("[TOP_CANDIDATE]",json.dumps(d["candidates"][0],sort_keys=True)[:1800])
  if not d["candidates"]:self.fail("NO_CANONICAL_POSTGRESQL_EVIDENCE_TABLES")
  self.assertTrue(any(x["has_canonical_json"] for x in d["candidates"]),msg="NO_CANONICAL_JSONB_TABLE")
  print("[PASS] OSI-041B canonical PostgreSQL evidence table classifier")
  print("[TRADER] Prioritizes Oracle's canonical JSONB warehouse instead of guessing flat Solana tables")
if __name__=="__main__":unittest.main()
