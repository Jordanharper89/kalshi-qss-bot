from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_026_targeted_pumpswap_rule_contract import match,RULE
FREEZE="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_freeze_ledger.json"
OUT="runtime_state/solana_opportunities/profitability_runtime/targeted_rule_freezes.json"
def build(root):
 root=Path(root);d=json.loads((root/FREEZE).read_text(encoding="utf-8"))
 rows=[]
 for x in d.get("frozen_setups",[]):
  if x.get("family")!="PUMP_SWAP":continue
  p=x.get("first_price",x.get("last_price"))
  if match(p):
   rows.append({"freeze_hash":x.get("freeze_hash"),"family":"PUMP_SWAP","market_address":x.get("market_address"),
    "input_asset":x.get("input_asset"),"output_asset":x.get("output_asset"),"freeze_unix":x.get("freeze_unix"),
    "first_price":p,"last_price":x.get("last_price"),"rule":RULE,"execution_authority":False})
 return {"revision":"SSR_027","matched_freeze_count":len(rows),"rows":rows,
  "selection_semantics":"RULE_FROZEN_BEFORE_NEW_FORWARD_OUTCOME_COLLECTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
