from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_027_targeted_rule_freeze_filter import build as targets
OOS="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"
OUT="runtime_state/solana_opportunities/profitability_runtime/targeted_rule_outcomes.json"
def build(root):
 root=Path(root);t=targets(root);d=json.loads((root/OOS).read_text(encoding="utf-8"))
 wanted={x["freeze_hash"] for x in t["rows"]};rows=[]
 for x in d.get("cases",[]):
  if x.get("freeze_hash") in wanted and x.get("family")=="PUMP_SWAP":
   rows.append({"freeze_hash":x.get("freeze_hash"),"market_address":x.get("market_address"),
    "freeze_unix":x.get("freeze_unix"),"later_observed_unix":x.get("later_observed_unix"),
    "gross_forward_return":x.get("gross_forward_return"),"later_trade_signature":x.get("later_trade_signature"),
    "execution_authority":False})
 vals=[float(x["gross_forward_return"]) for x in rows if isinstance(x.get("gross_forward_return"),(int,float))]
 return {"revision":"SSR_028","targeted_case_count":len(vals),
  "mean_gross_return":None if not vals else sum(vals)/len(vals),
  "positive_frequency":None if not vals else sum(v>0 for v in vals)/len(vals),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
