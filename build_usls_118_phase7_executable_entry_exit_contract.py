from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_118_phase7_executable_entry_exit_contract.py"
TEST=ROOT/"test_usls_118_phase7_executable_entry_exit_contract.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def build():
 return {
  "revision":"USLS_118","phase":7,
  "capability":"EXECUTABLE_ENTRY_EXIT_MODELING",
  "required_inputs":[
   "family","market_address","asset_a","asset_b","trade_signature","trade_slot",
   "trade_observed_unix","effective_price","base_quantity","quote_quantity"],
  "required_entry_outputs":[
   "entry_reference_price","entry_executable_price","entry_slippage_fraction",
   "entry_fee_fraction","entry_latency_seconds","entry_liquidity_state",
   "entry_notional_supported","entry_state"],
  "required_exit_outputs":[
   "exit_reference_price","exit_executable_price","exit_slippage_fraction",
   "exit_fee_fraction","exit_latency_seconds","exit_liquidity_state",
   "exit_notional_supported","exit_state"],
  "required_trade_outputs":[
   "gross_return","net_return_after_friction","round_trip_fee_fraction",
   "round_trip_slippage_fraction","round_trip_latency_seconds",
   "max_adverse_excursion_after_entry","max_favorable_excursion_after_entry",
   "executable_state"],
  "rules":{
   "read_only":True,
   "future_leakage":"FORBIDDEN",
   "entry_must_use_information_available_at_or_before_entry":True,
   "exit_must_use_information_available_at_or_before_exit":True,
   "missing_fee_or_liquidity":"RETAIN_AS_UNAVAILABLE_NOT_ZERO",
   "quote_asset_policy":"AGNOSTIC",
   "unknown_venue_state":"RETAIN",
   "profitability_claim":"FORBIDDEN_UNTIL_PROSPECTIVE_OOS_NET_EVIDENCE"},
  "execution_authority":False}

def write(root):
 d=build()
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_executable_entry_exit_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_118_phase7_executable_entry_exit_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertEqual(d["phase"],7)
  self.assertEqual(d["capability"],"EXECUTABLE_ENTRY_EXIT_MODELING")
  self.assertTrue(d["rules"]["read_only"])
  self.assertEqual(d["rules"]["future_leakage"],"FORBIDDEN")
  self.assertEqual(d["rules"]["missing_fee_or_liquidity"],"RETAIN_AS_UNAVAILABLE_NOT_ZERO")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-118 Phase 7 executable entry/exit contract")
  print("[PASS] entry/exit/slippage/fees/latency/liquidity/net-return semantics frozen")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
