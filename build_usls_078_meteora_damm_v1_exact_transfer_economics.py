from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_078_meteora_damm_v1_exact_transfer_economics.py"
TEST=ROOT/"test_usls_078_meteora_damm_v1_exact_transfer_economics.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def parent(level,ordinal):
 return int(str(level).split(":",1)[1]) if str(level).startswith("inner:") else int(ordinal)

def keylist(tx):
 msg=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in msg.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])

def token_meta(tx):
 ks=keylist(tx);out={}
 for name in ("preTokenBalances","postTokenBalances"):
  for x in ((tx or {}).get("meta") or {}).get(name) or []:
   i=x.get("accountIndex");u=x.get("uiTokenAmount") or {}
   if isinstance(i,int) and i<len(ks) and x.get("mint"):
    out[ks[i]]={"mint":x["mint"],"decimals":int(u.get("decimals") or 0)}
 return out

def transfers(tx,p,meta):
 out=[]
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")!=p:continue
  for ix in g.get("instructions") or []:
   q=ix.get("parsed")
   if not isinstance(q,dict) or q.get("type") not in ("transfer","transferChecked","transferCheckedWithFee"):continue
   info=q.get("info") or {};src=info.get("source");dst=info.get("destination");ta=info.get("tokenAmount")
   if isinstance(ta,dict) and ta.get("amount") is not None:amt=int(ta["amount"])/(10**int(ta.get("decimals") or 0))
   elif info.get("amount") is not None and src in meta:amt=int(info["amount"])/(10**meta[src]["decimals"])
   else:amt=None
   out.append({"source":src,"destination":dst,"amount":amt})
 return out

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"meteora_damm_v1_exact_swaps.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  m=token_meta(x["transaction"]);ts=transfers(x["transaction"],parent(x["level"],x["instruction_ordinal"]),m)
  ins=[t["amount"] for t in ts if t["source"]==x["user_source"] and t["amount"] is not None]
  outs=[t["amount"] for t in ts if t["destination"]==x["user_destination"] and t["amount"] is not None]
  im=m.get(x["user_source"],{}).get("mint");om=m.get(x["user_destination"],{}).get("mint")
  ia=sum(ins) if ins else None;oa=sum(outs) if outs else None;exact=bool(im and om and ia and oa)
  rows.append({"signature":x["signature"],"pool":x["pool"],"trader":x["trader"],"input_mint":im,
   "input_amount":ia,"output_mint":om,"output_amount":oa,
   "decoder_state":"EXACT_DAMM_V1_INSTRUCTION_ECONOMICS" if exact else "TRANSFER_RECONCILIATION_PENDING",
   "execution_authority":False})
 return {"revision":"USLS_078","row_count":len(rows),
  "exact_economic_count":sum(x["decoder_state"].startswith("EXACT_DAMM_V1") for x in rows),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_damm_v1_exact_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_078_meteora_damm_v1_exact_transfer_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"][:20]:print("[ECON]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertGreater(d["exact_economic_count"],0,"NO_EXACT_DAMM_V1_ECONOMICS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-078 DAMM v1 exact instruction-level transfer economics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
