from __future__ import annotations
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
