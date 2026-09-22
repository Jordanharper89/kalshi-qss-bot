from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_083_orca_exact_mint_decimal_economics.py"
TEST=ROOT/"test_usls_083_orca_exact_mint_decimal_economics.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
def keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])
def meta(tx):
 ks=keys(tx);o={}
 for n in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(n) or []:
   i=x.get("accountIndex");u=x.get("uiTokenAmount") or {}
   if isinstance(i,int) and i<len(ks) and x.get("mint"):o[ks[i]]={"mint":x["mint"],"decimals":int(u.get("decimals") or 0)}
 return o
def scale(raw,acct,tm):
 z=tm.get(acct);return (raw/(10**z["decimals"]),z["mint"]) if z and raw is not None else (None,None)

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 ix=json.loads((b/"meteora_orca_exact_swap_instructions.json").read_text(encoding="utf-8"))
 rr=json.loads((b/"meteora_orca_exact_transfer_reconciliation.json").read_text(encoding="utf-8"))
 by={(x["signature"],x["instruction_ordinal"],x["level"]):x for x in ix["rows"] if x["venue"]=="ORCA"};rows=[]
 for r in rr["rows"]:
  if r["venue"]!="ORCA" or not r["economics"]:continue
  matches=[x for x in by.values() if x["signature"]==r["signature"]]
  x=matches[0] if len(matches)==1 else None
  if not x:continue
  a=x["accounts"];tm=meta(x["transaction"]);direction=r["economics"].get("direction")
  user_a,user_b=a[3],a[5]
  if direction=="A_TO_B":
   ia,im=scale(r["economics"]["input_amount"],user_a,tm);oa,om=scale(r["economics"]["output_amount"],user_b,tm)
  else:
   ia,im=scale(r["economics"]["input_amount"],user_b,tm);oa,om=scale(r["economics"]["output_amount"],user_a,tm)
  exact=bool(im and om and ia is not None and oa is not None)
  rows.append({"signature":r["signature"],"pool":r["pool"],"trader":r["trader"],"direction":direction,
   "input_mint":im,"input_amount":ia,"output_mint":om,"output_amount":oa,
   "decoder_state":"EXACT_ORCA_MINT_DECIMAL_ECONOMICS" if exact else "ORCA_MINT_DECIMAL_PENDING","execution_authority":False})
 return {"revision":"USLS_083","row_count":len(rows),"exact_economic_count":sum(x["decoder_state"].startswith("EXACT_") for x in rows),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/orca_exact_mint_decimal_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_083_orca_exact_mint_decimal_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_orca(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:print("[ORCA]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertEqual(d["exact_economic_count"],d["row_count"],"ORCA_MINT_DECIMAL_ECONOMICS_INCOMPLETE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-083 Orca exact mint + decimal-normalized economics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
