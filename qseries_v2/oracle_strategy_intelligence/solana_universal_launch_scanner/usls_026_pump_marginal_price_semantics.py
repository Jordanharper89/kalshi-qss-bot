from __future__ import annotations
import json,time,urllib.error,urllib.request
from pathlib import Path
RPC="https://api.mainnet-beta.solana.com"
WSOL="So11111111111111111111111111111111111111112"

def _rpc(method,params):
 delay=.75
 for attempt in range(5):
  body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
  req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
  try:
   with urllib.request.urlopen(req,timeout=20) as r:return json.loads(r.read()).get("result")
  except urllib.error.HTTPError as e:
   if e.code!=429:raise
  if attempt<4:time.sleep(delay);delay=min(delay*2,6)
 raise RuntimeError("RPC_RETRY_EXHAUSTED")

def _decimals(mint):
 if mint==WSOL:return 9
 r=_rpc("getTokenSupply",[mint,{"commitment":"confirmed"}])
 return int(((r or {}).get("value") or {}).get("decimals"))

def build(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"pump_bonding_curve_states.json").read_text(encoding="utf-8"))
 cache={};rows=[]
 for x in d["rows"]:
  s=x["state"];token=x["token_address"];quote=x["quote_mint"]
  if token not in cache:cache[token]=_decimals(token)
  if quote not in cache:cache[quote]=_decimals(quote)
  bd,qd=cache[token],cache[quote]
  vt=s["virtual_token_reserves"];vq=s["virtual_quote_reserves"]
  price=((vq/(10**qd))/(vt/(10**bd))) if vt else None
  rows.append({"event_id":x["event_id"],"token_address":token,"quote_mint":quote,
   "base_decimals":bd,"quote_decimals":qd,"virtual_token_reserves":vt,
   "virtual_quote_reserves":vq,"marginal_quote_per_token":price,
   "semantics":"BONDING_CURVE_MARGINAL_RESERVE_PRICE_PRE_FEE_NOT_EXECUTABLE_PNL",
   "profitability_eligible":False,"execution_authority":False})
 return {"revision":"USLS_026","row_count":len(rows),"rows":rows,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_marginal_prices.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
