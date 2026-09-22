from __future__ import annotations
import json
from pathlib import Path

def _load(root,name):
 return json.loads((Path(root)/name).read_text(encoding="utf-8"))

def run(root):
 lat=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_per_row_latency_recovery.json")
 dev=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_pretrade_reference_execution_deviation.json")
 ps=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase7_pumpswap_fee_liquidity_normalized.json")
 lidx={x["trade_signature"]:x for x in lat.get("rows",[])}
 didx={x["trade_signature"]:x for x in dev.get("rows",[])}
 rows=[]
 for x in ps.get("rows",[]):
  sig=x.get("trade_signature");l=lidx.get(sig,{});d=didx.get(sig,{})
  fee=x.get("fee_fraction_of_quote_notional");liq=x.get("quote_reserve_liquidity")
  latency=l.get("observation_latency_seconds")
  deviation=d.get("realized_execution_deviation_fraction")
  ref=d.get("pre_trade_reference_price")
  ready=all(v is not None for v in (x.get("effective_price"),fee,liq,latency,deviation,ref))
  rows.append({"family":"PUMP_SWAP","trade_signature":sig,"market_address":x.get("market_address"),
   "effective_price":x.get("effective_price"),"pre_trade_reference_price":ref,
   "realized_execution_deviation_fraction":deviation,
   "fee_fraction":fee,"quote_reserve_liquidity":liq,
   "observation_latency_seconds":latency,
   "executable_ready":ready,
   "readiness_basis":"OBSERVED_EXECUTION_PRICE_PLUS_PHYSICAL_FEE_LIQUIDITY_LATENCY_PLUS_BOUNDED_PRIOR_REFERENCE",
   "execution_authority":False})
 ready=[x for x in rows if x["executable_ready"]]
 return {"revision":"USLS_131","row_count":len(rows),"ready_count":len(ready),
  "ready_rows":ready,"rows":rows,
  "slippage_semantics":"REALIZED_EXECUTION_DEVIATION_CONSERVATIVE_PROXY_NOT_PURE_AMM_PRICE_IMPACT",
  "next_boundary":"FIRST_NET_EXECUTABLE_ROUND_TRIP_MODEL",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
