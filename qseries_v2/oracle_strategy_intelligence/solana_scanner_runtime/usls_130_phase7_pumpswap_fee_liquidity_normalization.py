from __future__ import annotations
import json
from pathlib import Path

SRC="runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json"

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def _rows(x):
 if isinstance(x,list):return x
 if isinstance(x,dict):
  for k in ("rows","trades","events","data"):
   if isinstance(x.get(k),list):return x[k]
 return []

def run(root):
 root=Path(root);raw=json.loads((root/SRC).read_text(encoding="utf-8"));src=_rows(raw)
 mints=sorted({str(x.get("quote_mint")) for x in src if x.get("quote_mint")})
 decimals={}
 for m in mints:
  try:
   z=_rpc("getTokenSupply",[m,{"commitment":"confirmed"}],20.0)
   val=(z or {}).get("value") if isinstance(z,dict) else None
   if isinstance(val,dict) and val.get("decimals") is not None:decimals[m]=int(val["decimals"])
  except Exception:pass
 out=[]
 for x in src:
  qmint=x.get("quote_mint");dec=decimals.get(str(qmint));q=x.get("quote_amount")
  try:q=float(q) if q is not None else None
  except Exception:q=None
  lp=x.get("lp_fee_raw");pf=x.get("protocol_fee_raw")
  try:fee_raw=float(lp or 0)+float(pf or 0)
  except Exception:fee_raw=None
  fee_quote=(fee_raw/(10**dec)) if fee_raw is not None and dec is not None else None
  fee_frac=(fee_quote/abs(q)) if fee_quote is not None and q not in (None,0) else None
  r=x.get("pool_quote_token_reserves_raw")
  try:liq=(float(r)/(10**dec)) if r is not None and dec is not None else None
  except Exception:liq=None
  out.append({"family":"PUMP_SWAP","trade_signature":x.get("signature"),
   "market_address":x.get("market_address"),"quote_mint":qmint,"quote_decimals":dec,
   "quote_amount":q,"network_independent_protocol_lp_fee_quote":fee_quote,
   "fee_fraction_of_quote_notional":fee_frac,"quote_reserve_liquidity":liq,
   "effective_price":x.get("effective_price"),"observed_unix":x.get("observed_unix"),
   "block_time":x.get("block_time"),"execution_authority":False})
 return {"revision":"USLS_130","row_count":len(out),"quote_mint_decimals":decimals,
  "fee_fraction_ready_count":sum(x["fee_fraction_of_quote_notional"] is not None for x in out),
  "liquidity_ready_count":sum(x["quote_reserve_liquidity"] is not None for x in out),
  "rows":out,"fee_semantics":"LP_PLUS_PROTOCOL_FEE_RAW_CONVERTED_WITH_PHYSICAL_QUOTE_MINT_DECIMALS",
  "next_boundary":"FIRST_STRICT_EXECUTABLE_READY_ROWS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_pumpswap_fee_liquidity_normalized.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
