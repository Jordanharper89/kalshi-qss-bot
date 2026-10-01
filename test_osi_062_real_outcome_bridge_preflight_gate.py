import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_062_real_outcome_bridge_preflight_gate import gate,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  d=gate(ROOT);p=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[COMPONENTS]",json.dumps(d["components_present"],sort_keys=True));print("[PENDING_CASES]",d["pending_case_count"]);print("[TEMPORAL_CALLABLES]",d["temporal_callable_count"]);print("[REAL_OUTCOME_BRIDGE_PREFLIGHT_READY]",d["real_outcome_bridge_preflight_ready"])
  if not d["real_outcome_bridge_preflight_ready"]:self.fail("REAL_OUTCOME_BRIDGE_PREFLIGHT_NOT_READY")
  print("[PASS] OSI-062 real outcome bridge preflight gate")
  print("[SCOPE] Preflight only; next build must physically pass real temporal records into OAD-314")
if __name__=="__main__":unittest.main()
