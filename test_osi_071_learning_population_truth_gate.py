import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_071_learning_population_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[SAMPLE_SIZE]",d["sample_size"]);print("[BY_HORIZON]",json.dumps(d["by_horizon"],sort_keys=True));print("[BY_CLASS]",json.dumps(d["by_class"],sort_keys=True))
  print("[POPULATION_INGESTION_READY]",d["population_ingestion_ready"]);print("[FORMULA_DISCOVERY_STATISTICALLY_READY]",d["formula_discovery_statistically_ready"])
  if not d["population_ingestion_ready"]:self.fail("NO_REAL_EMPIRICAL_LEARNING_POPULATION")
  print("[PASS] OSI-071 learning population truth gate")
  print("[SCOPE] PASS does not claim enough samples for formula discovery")
if __name__=="__main__":unittest.main()
