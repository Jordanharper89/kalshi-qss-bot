from __future__ import annotations
import json
from pathlib import Path

def load(root,name):
 p=Path(root)/name
 return json.loads(p.read_text(encoding="utf-8"))

def run(root):
 contract=load(root,"runtime_state/solana_opportunities/solana_scanner/phase6_universal_price_path_contract.json")
 econ=load(root,"runtime_state/solana_opportunities/solana_scanner/pump_exact_trade_economic_path.json")
 paths=load(root,"runtime_state/solana_opportunities/solana_scanner/continuous_market_price_paths.json")
 reg=load(root,"runtime_state/solana_opportunities/solana_scanner/cross_venue_path_adapter_registry.json")
 covered=[k for k,v in reg["family_module_counts"].items() if v>0]
 pump_ready=(econ.get("priced_trade_count",0)>0 and paths.get("path_count",0)>0)
 return {"revision":"USLS_112","phase":6,
  "reference_venue":"PUMP_FUN","reference_path_physically_proven":pump_ready,
  "continuous_between_horizons":paths.get("continuous_between_horizons"),
  "priced_trade_count":econ.get("priced_trade_count",0),
  "reference_path_count":paths.get("path_count",0),
  "decoder_pavement_families":covered,
  "decoder_pavement_family_count":len(covered),
  "phase6_status":"IN_PROGRESS",
  "remaining_required_capability":"WIRE_ALL_CERTIFIED_DEX_FAMILIES_TO_UNIVERSAL_PRICE_PATH",
  "phase6_physically_certified":False,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase6_reference_path_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
