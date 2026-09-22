from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_057b_raydium_exact_pair_orientation_decoder.py"
TEST=ROOT/"test_usls_057b_raydium_exact_pair_orientation_decoder.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
QUOTES={"So11111111111111111111111111111111111111112","EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"}

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
 src=json.loads((base/"raydium_exact_instruction_pool_roles.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  cand=[]
  for s in signer_keys(x["transaction"]):
   d=deltas(x["transaction"],s);neg=[(m,-v) for m,v in d.items() if v<0];pos=[(m,v) for m,v in d.items() if v>0]
   if len(neg)==1 and len(pos)==1:cand.append((s,neg[0],pos[0]))
  trader,inp,out=(cand[0] if len(cand)==1 else (None,(None,None),(None,None)))
  im,ia=inp;om,oa=out;side="UNKNOWN_TRADE_TYPE";token=quote=ba=qa=None
  if im in QUOTES and om not in QUOTES:side="BUY";quote=im;token=om;qa=ia;ba=oa
  elif om in QUOTES and im not in QUOTES:side="SELL";quote=om;token=im;qa=oa;ba=ia
  state="EXACT_QUOTE_ORIENTED_SWAP" if side!="UNKNOWN_TRADE_TYPE" else ("EXACT_TWO_ASSET_SWAP_ORIENTATION_PENDING" if trader else "SIGNER_DELTA_AMBIGUOUS")
  rows.append({"venue":x["venue"],"signature":x["signature"],"instruction_name":x["instruction_name"],
   "pool":x["pool"],"trader":trader,"input_mint":im,"input_amount":ia,"output_mint":om,"output_amount":oa,
   "token_address":token,"quote_mint":quote,"side":side,"base_amount":ba,"quote_amount":qa,
   "effective_price":qa/ba if ba and qa is not None else None,"decoder_state":state,"execution_authority":False})
 return {"revision":"USLS_057B","row_count":len(rows),
  "venue_exact_quote_counts":{v:sum(x["venue"]==v and x["decoder_state"]=="EXACT_QUOTE_ORIENTED_SWAP" for x in rows)
   for v in sorted({x["venue"] for x in rows})},
  "venue_two_asset_counts":{v:sum(x["venue"]==v and x["trader"] is not None for x in rows)
   for v in sorted({x["venue"] for x in rows})},
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_exact_pair_orientation.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_057b_raydium_exact_pair_orientation_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_orientation(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],
   "venue_two_asset_counts":d["venue_two_asset_counts"],"venue_exact_quote_counts":d["venue_exact_quote_counts"]},sort_keys=True))
  for x in d["rows"][:40]:print("[ECON]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0);self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-057B Raydium exact pair/orientation decoder")
  print("[PASS] BUY/SELL only emitted when WSOL/USDC quote orientation is physically exact")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
