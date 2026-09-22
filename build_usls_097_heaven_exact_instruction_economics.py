from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_097_heaven_exact_instruction_economics.py"
TEST=ROOT/"test_usls_097_heaven_exact_instruction_economics.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
def parent(level,ordinal):return int(str(level).split(":",1)[1]) if str(level).startswith("inner:") else int(ordinal)
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
def tok(tx,p,tm):
 out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=p:continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict) or q.get("type") not in ("transfer","transferChecked","transferCheckedWithFee"):continue
   i=q.get("info") or {}
   if i.get("lamports") is not None:continue
   s=i.get("source");d=i.get("destination");ta=i.get("tokenAmount")
   if isinstance(ta,dict) and ta.get("amount") is not None:a=int(ta["amount"])/(10**int(ta.get("decimals") or 0))
   elif i.get("amount") is not None and (tm.get(s) or tm.get(d)):z=tm.get(s) or tm.get(d);a=int(i["amount"])/(10**z["decimals"])
   else:a=None
   out.append((s,d,a))
 return out
def total(rows,s,d):
 v=[a for x,y,a in rows if x==s and y==d and a is not None];return sum(v) if v else None

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_account_roles.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  if x["venue"]!="HEAVEN":continue
  r=x["roles"];tm=meta(x["transaction"]);t=tok(x["transaction"],parent(x["level"],x["instruction_ordinal"]),tm)
  if x["side"]=="BUY":
   ia=total(t,r["user_token_b_vault"],r["token_b_vault"]);oa=total(t,r["token_a_vault"],r["user_token_a_vault"])
   im=r["token_b_mint"];om=r["token_a_mint"]
  else:
   ia=total(t,r["user_token_a_vault"],r["token_a_vault"]);oa=total(t,r["token_b_vault"],r["user_token_b_vault"])
   im=r["token_a_mint"];om=r["token_b_mint"]
  exact=bool(ia is not None and oa is not None and ia>0 and oa>0)
  rows.append({"signature":x["signature"],"side":x["side"],"market_address":r["liquidity_pool_state"],"trader":r["user"],
   "input_asset":im,"input_amount":ia,"output_asset":om,"output_amount":oa,
   "decoder_state":"EXACT_HEAVEN_INSTRUCTION_ECONOMICS" if exact else "HEAVEN_RECONCILIATION_PENDING","execution_authority":False})
 return {"revision":"USLS_097","row_count":len(rows),"exact_economic_count":sum(x["decoder_state"].startswith("EXACT_") for x in rows),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/heaven_exact_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_097_heaven_exact_instruction_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:
   if not x["decoder_state"].startswith("EXACT_"):print("[PENDING]",json.dumps(x,sort_keys=True))
  self.assertEqual(d["row_count"],59);self.assertEqual(d["exact_economic_count"],d["row_count"],"HEAVEN_EXACT_ECONOMICS_INCOMPLETE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-097 Heaven exact A/B-vault instruction economics 59/59")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
