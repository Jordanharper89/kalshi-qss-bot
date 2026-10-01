import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_042_bounded_solana_postgresql_sample_reader import read
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=read(ROOT,25);self.assertFalse(d["execution_authority"])
  print("[TABLE]",d["table"]);print("[DSN_ENV]",d.get("dsn_env"));print("[ROWS]",d["row_count"])
  if d["rows"]:print("[SAMPLE_KEYS]",json.dumps(sorted(d["rows"][0].keys())));print("[SOURCE_ID]",d["rows"][0].get("source_id"));print("[OBSERVATION_TYPE]",d["rows"][0].get("observation_type"))
  if not d["rows"]:self.fail("NO_CANONICAL_POSTGRESQL_ROWS")
  print("[PASS] OSI-042B bounded canonical PostgreSQL reader")
  print("[TRADER] Reads a small recent slice from Oracle's canonical warehouse using the existing root credential")
if __name__=="__main__":unittest.main()
