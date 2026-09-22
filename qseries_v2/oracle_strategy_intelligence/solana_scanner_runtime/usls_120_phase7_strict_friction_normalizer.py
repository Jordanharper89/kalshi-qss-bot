from __future__ import annotations
import json,math
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

def _num(v):
 try:
  x=float(v)
  return x if math.isfinite(x) else None
 except Exception:return None

def run(root):
 root=Path(root)
 d=json.loads((root/SRC).read_text(encoding="utf-8"))
 out=[];fam={}
 for x in d.get("rows",[]):
  price=_num(x.get("effective_price"))
  b=_num(x.get("base_quantity"));q=_num(x.get("quote_quantity"))
  if price is None or price<=0:continue
  # Strictly preserve unavailable friction terms as None.
  row={"family":x.get("family"),"market_address":x.get("market_address"),
   "asset_a":x.get("asset_a"),"asset_b":x.get("asset_b"),
   "trade_signature":x.get("trade_signature"),"trade_slot":x.get("trade_slot"),
   "trade_observed_unix":x.get("trade_observed_unix"),
   "reference_price":price,"base_quantity":b,"quote_quantity":q,
   "fee_fraction":None,"slippage_fraction":None,"latency_seconds":None,
   "liquidity_notional":None,"friction_state":"UNAVAILABLE_UNLESS_PHYSICALLY_SUPPORTED",
   "source_artifact":x.get("source_artifact"),"execution_authority":False}
  out.append(row);fam[row["family"]]=fam.get(row["family"],0)+1
 return {"revision":"USLS_120","row_count":len(out),"family_row_counts":fam,"rows":out,
  "missing_values_are_zero":False,
  "friction_unknown_policy":"RETAIN_NULL_NOT_ZERO",
  "next_boundary":"EXECUTABLE_ENTRY_EXIT_BASELINE_MODEL",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_friction_normalized_rows.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
