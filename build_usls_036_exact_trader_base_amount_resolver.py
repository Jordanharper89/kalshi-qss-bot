from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_036_exact_trader_base_amount_resolver.py"
TEST=ROOT/"test_usls_036_exact_trader_base_amount_resolver.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

def _signers(tx):
 keys=(((tx.get("transaction") or {}).get("message") or {}).get("accountKeys") or [])
 return [k.get("pubkey") for k in keys if isinstance(k,dict) and k.get("signer") and k.get("pubkey")]

def _token_owner_deltas(tx,mint):
 meta=tx.get("meta") or {};pre=meta.get("preTokenBalances") or [];post=meta.get("postTokenBalances") or []
 vals=defaultdict(lambda:[0,0,None])
 for side,rows in ((0,pre),(1,post)):
  for x in rows:
   if x.get("mint")!=mint or not x.get("owner"):continue
   u=x.get("uiTokenAmount") or {};amt=int(u.get("amount") or 0);dec=u.get("decimals")
   vals[x["owner"]][side]+=amt
   if dec is not None:vals[x["owner"]][2]=int(dec)
 out={}
 for owner,(a,b,dec) in vals.items():
  out[owner]={"raw_delta":b-a,"decimals":dec,
   "ui_delta":None if dec is None else (b-a)/(10**dec)}
 return out

def resolve(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_trade_raw_transactions.json").read_text(encoding="utf-8"))
 rows=[]
 for x in src["rows"]:
  tx=x["raw_transaction"] or {};signers=_signers(tx);deltas=_token_owner_deltas(tx,x["token_address"])
  candidates=[s for s in signers if s in deltas and deltas[s]["raw_delta"]!=0]
  trader=candidates[0] if len(candidates)==1 else None
  info=deltas.get(trader) if trader else None
  delta=None if info is None else info["ui_delta"]
  direction_ok=(delta is not None and ((x["side"]=="BUY" and delta>0) or (x["side"]=="SELL" and delta<0)))
  rows.append({"trade_id":x["trade_id"],"signature":x["signature"],"side":x["side"],
   "token_address":x["token_address"],"market_address":x["market_address"],"quote_mint":x["quote_mint"],
   "birth_age_seconds":x["birth_age_seconds"],"trader":trader,
   "base_amount":abs(delta) if direction_ok else None,"signed_base_delta":delta if direction_ok else None,
   "base_decimals":None if info is None else info["decimals"],
   "signer_count":len(signers),"candidate_trader_count":len(candidates),
   "direction_check":direction_ok,"decoder_state":"TRADER_AND_BASE_EXACT" if trader and direction_ok else "TRADER_OR_BASE_UNRESOLVED",
   "execution_authority":False})
 return {"revision":"USLS_036","row_count":len(rows),
  "resolved_count":sum(1 for x in rows if x["decoder_state"]=="TRADER_AND_BASE_EXACT"),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=resolve(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_trade_participants_amounts.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_036_exact_trader_base_amount_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_resolve(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"resolved_count":d["resolved_count"]},sort_keys=True))
  for x in d["rows"]:print("[TRADE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(d["resolved_count"],0)
  self.assertTrue(all(x["base_amount"] is None or x["base_amount"]>0 for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-036 exact trader + base-token amount evidence resolved where physically provable")
  print("[PASS] unresolved trades remain explicit; no participant or amount guessing")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
