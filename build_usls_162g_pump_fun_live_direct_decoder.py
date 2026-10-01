from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_162g_pump_fun_live_direct_decoder.py"
TEST=ROOT/"test_usls_162g_pump_fun_live_direct_decoder.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162f_pump_trade_market_role_audit import instructions
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_040_pump_trade_event_exact_decoder import events
AUD="runtime_state/solana_opportunities/solana_scanner/pump_trade_market_role_audit.json"
WSOL="So11111111111111111111111111111111111111112"
def token_decimals(tx,mint):
 for name in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(name) or []:
   if x.get("mint")==mint:
    u=x.get("uiTokenAmount") or {}
    if u.get("decimals") is not None:return int(u["decimals"])
 return None
def decode(root,signature,tx,observed_unix):
 a=json.loads((Path(root)/AUD).read_text(encoding="utf-8"));roles=a.get("roles") or {};out=[]
 for level,ordinal,c,ac in instructions(tx):
  name=c.get("instruction_name");side=c.get("side");r=roles.get(name)
  if not r or not r.get("certified") or r["market_account_index"]>=len(ac):continue
  market=ac[r["market_account_index"]];ev=[e for e in events(tx) if e.get("side")==side]
  if len(ev)!=1:continue
  e=ev[0];dec=token_decimals(tx,e["mint"])
  if dec is None:continue
  token=float(e["token_amount_raw"])/(10**dec);sol=float(e["sol_amount_lamports"])/1_000_000_000
  if token<=0 or sol<=0:continue
  if side=="BUY":ia,iamt,oa,oamt=WSOL,sol,e["mint"],token
  else:ia,iamt,oa,oamt=e["mint"],token,WSOL,sol
  out.append({"family":"PUMP_FUN","trade_signature":signature,"market_address":market,"token_address":e["mint"],
   "input_asset":ia,"input_amount":iamt,"output_asset":oa,"output_amount":oamt,
   "effective_output_per_input":oamt/iamt,"side":side,"trader":e["user"],"token_decimals":dec,
   "observed_unix":float(observed_unix),"strict_live_provenance":True,
   "economics_method":"EXACT_TRADE_EVENT_PLUS_CERTIFIED_INSTRUCTION_MARKET_ROLE","execution_authority":False})
 return out
def contract(root):
 a=json.loads((Path(root)/AUD).read_text(encoding="utf-8"))
 return {"revision":"USLS_162G","family":"PUMP_FUN","market_role_certified":a.get("all_observed_trade_types_certified"),
  "roles":a.get("roles"),"economics_source":"USLS_040_EXACT_TRADE_EVENT",
  "token_decimals_source":"TRANSACTION_TOKEN_BALANCES","profitability_claimed":False,"execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_162g_pump_fun_live_direct_decoder import contract
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  d=contract(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["market_role_certified"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-162G Pump.fun live direct decoder contract")
  print("[NEXT] PUMP_FUN_STRICT_LIVE_ECONOMICS_CAPTURE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
