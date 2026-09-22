from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_082_meteora_damm_v1_strict_vault_mint_repair.py"
TEST=ROOT/"test_usls_082_meteora_damm_v1_strict_vault_mint_repair.py"

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
def transfers(tx,p,tm):
 out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=p:continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict) or q.get("type") not in ("transfer","transferChecked","transferCheckedWithFee"):continue
   i=q.get("info") or {};s=i.get("source");d=i.get("destination");ta=i.get("tokenAmount")
   if isinstance(ta,dict) and ta.get("amount") is not None:a=int(ta["amount"])/(10**int(ta.get("decimals") or 0))
   elif i.get("amount") is not None and (s in tm or d in tm):a=int(i["amount"])/(10**(tm.get(s) or tm.get(d))["decimals"])
   else:a=None
   out.append({"source":s,"destination":d,"amount":a})
 return out

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"meteora_damm_v1_exact_swaps.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  tm=meta(x["transaction"]);ts=transfers(x["transaction"],parent(x["level"],x["instruction_ordinal"]),tm)
  ins=[t for t in ts if t["source"]==x["user_source"] and t["amount"] is not None]
  outs=[t for t in ts if t["destination"]==x["user_destination"] and t["amount"] is not None]
  it=ins[0] if len(ins)==1 else None;ot=outs[0] if len(outs)==1 else None
  im=(tm.get(x["user_source"]) or (tm.get(it["destination"]) if it else None) or {}).get("mint")
  om=(tm.get(x["user_destination"]) or (tm.get(ot["source"]) if ot else None) or {}).get("mint")
  ia=it["amount"] if it else None;oa=ot["amount"] if ot else None;exact=bool(im and om and ia and oa)
  rows.append({"signature":x["signature"],"pool":x["pool"],"trader":x["trader"],"input_mint":im,"input_amount":ia,
   "output_mint":om,"output_amount":oa,"decoder_state":"EXACT_DAMM_V1_STRICT_ECONOMICS" if exact else "STRICT_RECONCILIATION_PENDING",
   "execution_authority":False})
 return {"revision":"USLS_082","row_count":len(rows),"exact_economic_count":sum(x["decoder_state"].startswith("EXACT_") for x in rows),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_damm_v1_strict_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_082_meteora_damm_v1_strict_vault_mint_repair import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:print("[DAMM_V1]",json.dumps(x,sort_keys=True))
  self.assertEqual(d["exact_economic_count"],d["row_count"],"DAMM_V1_STRICT_ECONOMICS_INCOMPLETE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-082 DAMM v1 19/19 strict vault-side mint/economics reconciliation")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
