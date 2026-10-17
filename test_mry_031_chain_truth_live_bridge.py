import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_runtime_parses(self):
  ast.parse(R.read_text(encoding="utf-8"))
 def test_chain_truth_live_bridge(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def fast_live_attack")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertIn("simulate_current(locked,USER)",f)
  self.assertIn("pump_6040_actual_base_out(sim)",f)
  self.assertIn("reprice_from_pump_chain_truth(snap,opportunity,actual)",f)
  self.assertIn("FAST_010_6040_REBUILD_PASS",f)
  self.assertEqual(f.count("lane.newer_waiting(token,generation)"),1)
 def test_no_blind_slippage_widening(self):
  s=R.read_text(encoding="utf-8")
  a=s.index("def fast_live_attack")
  b=s.index("\ndef ",a+5)
  f=s[a:b]
  self.assertNotIn("FAST_010_PUMP_EXECUTION_TOLERANCE_BPS",f)
  self.assertIn("corrected_after<FAST_010_MIN_REALIZED_LAMPORTS",f)
 def test_money_and_send_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__": unittest.main(verbosity=2)
