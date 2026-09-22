from __future__ import annotations
import json
from pathlib import Path

def build():
 return {
  "revision":"USLS_153","phase":8,"capability":"CROSS_LAUNCH_FEATURE_LEARNING",
  "feature_families":[
   "trade_velocity","quote_volume_velocity","buy_sell_imbalance",
   "unique_trader_growth","repeat_trader_fraction","concentration",
   "price_path_momentum","mfe_mae","liquidity_change",
   "execution_deviation","latency","fee_load"],
  "horizons_seconds":[1,5,15,30,60,300,900],
  "learning_rules":{
   "future_leakage":"FORBIDDEN",
   "features_must_exist_at_or_before_prediction_time":True,
   "outcomes_must_be_strictly_after_prediction_time":True,
   "missing_feature":"RETAIN_NULL",
   "raw_frequency_is_not_calibrated_probability":True,
   "cross_venue_orientation":"DIRECTED_ASSET_PAIR_PRESERVED",
   "profitability_claim":"FORBIDDEN_WITHOUT_PROSPECTIVE_OOS_NET_EVIDENCE"},
  "phase7_dependency_state":"PARTIAL_EXECUTABLE_SUPPORT_ALLOWED_ONLY_AS_EXPLICIT_FEATURE_AVAILABILITY",
  "read_only":True,"execution_authority":False}

def write(root):
 d=build()
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_cross_launch_feature_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
