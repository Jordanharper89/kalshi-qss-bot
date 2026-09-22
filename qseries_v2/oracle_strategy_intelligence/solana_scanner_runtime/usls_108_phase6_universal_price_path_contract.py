from __future__ import annotations
import json
from pathlib import Path

HORIZONS=(1,5,15,30,60,300,900)

def build():
 return {
  "revision":"USLS_108",
  "phase":6,
  "capability":"CONTINUOUS_PRICE_PATH_RECONSTRUCTION",
  "input_contract":{
   "required":["family","token_address","market_address","trade_signature","trade_slot",
               "trade_observed_unix","side","base_quantity","quote_quantity"],
   "optional":["effective_price","liquidity","reserves_before","reserves_after",
               "fee","priority_fee","source_lineage"]},
  "path_contract":{
   "standard_horizons_seconds":list(HORIZONS),
   "continuous_between_horizons":True,
   "required_outputs":["market_key","birth_anchor","first_trade","last_trade","trade_count",
     "price_path","mfe","mae","high_price","low_price","last_price","volume_base",
     "volume_quote","buy_count","sell_count","unknown_side_count","freshness_seconds"]},
  "semantics":{
   "price_kind":"OBSERVED_EFFECTIVE_PRICE_NOT_EXECUTABLE_PNL",
   "mfe_mae_anchor":"FIRST_VALID_OBSERVED_TRADE_AFTER_EXACT_BIRTH",
   "unknown_side":"RETAIN",
   "missing_price":"RETAIN_EVENT_EXCLUDE_FROM_PRICE_STATISTICS",
   "future_leakage":"FORBIDDEN"},
  "venue_policy":"ONE_UNIVERSAL_PATH_SCHEMA_PROTOCOL_SPECIFIC_DECODERS",
  "phase5_dependency":"EXACT_BIRTH_TO_TRADE_LIFECYCLE",
  "profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build()
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase6_universal_price_path_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
