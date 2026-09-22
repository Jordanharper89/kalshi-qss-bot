from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_026_pump_marginal_price_semantics.py"
TEST=ROOT/"test_usls_026_pump_marginal_price_semantics.py"

MOD_TEXT=r"""from __future__ import annotations
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
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_026_pump_marginal_price_semantics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_price(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["rows"]:print("[PRICE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertTrue(all(x["marginal_quote_per_token"] is not None and x["marginal_quote_per_token"]>0 for x in d["rows"]))
  self.assertTrue(all(not x["profitability_eligible"] for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-026 Pump marginal price semantics certified")
  print("[PASS] reserve-derived price is explicitly blocked from executable-profit claims")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
