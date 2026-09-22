from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_062_launchlab_exact_account_economics.py"
TEST=ROOT/"test_usls_062_launchlab_exact_account_economics.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_060_launchlab_official_trade_contract import roles

def signer_keys(tx):
 ks=(((tx or {}).get("transaction") or {}).get("message") or {}).get("accountKeys") or []
 return [x.get("pubkey") for x in ks if isinstance(x,dict) and x.get("signer") and x.get("pubkey")]

def deltas(tx,owner):
 meta=(tx or {}).get("meta") or {};z=defaultdict(lambda:[0,0,None])
 for j,rows in ((0,meta.get("preTokenBalances") or []),(1,meta.get("postTokenBalances") or [])):
  for x in rows:
   if x.get("owner")!=owner or not x.get("mint"):continue
   u=x.get("uiTokenAmount") or {};z[x["mint"]][j]+=int(u.get("amount") or 0);z[x["mint"]][2]=u.get("decimals")
 return {m:(b-a)/(10**int(d)) for m,(a,b,d) in z.items() if d is not None and b!=a}

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"launchlab_deep_trade_census.json").read_text(encoding="utf-8"));out=[]
 for x in src["rows"]:
  r=roles(x["accounts"]);payer=r["payer"];d=deltas(x["transaction"],payer)
  base=r["base_token_mint"];quote=r["quote_token_mint"]
  bd=d.get(base);qd=d.get(quote)
  exact=bd is not None and qd is not None and bd>0 and qd<0
  out.append({"signature":x["signature"],"instruction_name":x["instruction_name"],
   "trader":payer,"pool":r["pool_state"],"base_mint":base,"quote_mint":quote,
   "user_base_token_account":r["user_base_token"],"user_quote_token_account":r["user_quote_token"],
   "base_vault":r["base_vault"],"quote_vault":r["quote_vault"],
   "base_amount":bd if exact else None,"quote_amount":-qd if exact else None,
   "effective_price":(-qd/bd) if exact and bd else None,"side":"BUY" if exact else "UNKNOWN_TRADE_TYPE",
   "decoder_state":"EXACT_LAUNCHLAB_BUY_ECONOMICS" if exact else "ACCOUNT_ROLE_EXACT_ECONOMICS_UNRESOLVED",
   "execution_authority":False})
 return {"revision":"USLS_062","row_count":len(out),
  "exact_economic_count":sum(x["decoder_state"]=="EXACT_LAUNCHLAB_BUY_ECONOMICS" for x in out),
  "rows":out,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/launchlab_exact_account_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_062_launchlab_exact_account_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:print("[ECON]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertEqual(d["exact_economic_count"],d["row_count"])
  self.assertTrue(all(x["pool"] and x["base_mint"] and x["quote_mint"] and x["effective_price"]>0 for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-062 LaunchLab exact account roles + BUY economics")
  print("[PASS] pool, base/quote mints, trader, exact amounts and effective price physically resolved")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")