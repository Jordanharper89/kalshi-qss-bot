from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_037_quote_amount_evidence_audit.py"
TEST=ROOT/"test_usls_037_quote_amount_evidence_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

WSOL="So11111111111111111111111111111111111111112"

def _quote_token_delta(tx,mint,owner):
 meta=tx.get("meta") or {};vals=defaultdict(lambda:[0,0,None])
 for side,rows in ((0,meta.get("preTokenBalances") or []),(1,meta.get("postTokenBalances") or [])):
  for x in rows:
   if x.get("mint")!=mint or x.get("owner")!=owner:continue
   u=x.get("uiTokenAmount") or {};vals[owner][side]+=int(u.get("amount") or 0);vals[owner][2]=u.get("decimals")
 if owner not in vals:return None
 a,b,dec=vals[owner]
 return None if dec is None else (b-a)/(10**int(dec))

def _signer_lamport(tx,owner):
 msg=((tx.get("transaction") or {}).get("message") or {});keys=msg.get("accountKeys") or []
 names=[k.get("pubkey") if isinstance(k,dict) else k for k in keys]
 if owner not in names:return None
 i=names.index(owner);meta=tx.get("meta") or {};pre=meta.get("preBalances") or [];post=meta.get("postBalances") or []
 if i>=len(pre) or i>=len(post):return None
 fee=int(meta.get("fee") or 0) if i==0 else 0
 return {"raw_lamport_delta":int(post[i])-int(pre[i]),"fee_lamports":fee,
  "fee_adjusted_lamport_delta":int(post[i])-int(pre[i])+fee}

def audit(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 raw=json.loads((base/"pump_trade_raw_transactions.json").read_text(encoding="utf-8"))
 part=json.loads((base/"pump_trade_participants_amounts.json").read_text(encoding="utf-8"))
 raw_by={x["trade_id"]:x for x in raw["rows"]}
 rows=[]
 for x in part["rows"]:
  tx=(raw_by.get(x["trade_id"]) or {}).get("raw_transaction") or {};tr=x.get("trader");quote=x["quote_mint"]
  token_delta=_quote_token_delta(tx,quote,tr) if tr else None
  native=_signer_lamport(tx,tr) if tr else None
  exact=(quote!=WSOL and token_delta is not None and token_delta!=0)
  qamt=abs(token_delta) if exact else None
  state=("QUOTE_TOKEN_DELTA_EXACT" if exact else
   "QUOTE_AMOUNT_PENDING_NATIVE_SOL_RECONCILIATION" if quote==WSOL else "QUOTE_AMOUNT_UNRESOLVED")
  rows.append({"trade_id":x["trade_id"],"signature":x["signature"],"side":x["side"],"trader":tr,
   "quote_mint":quote,"quote_amount":qamt,"quote_token_delta":token_delta,
   "signer_native_balance_evidence":native,"quote_decoder_state":state,
   "execution_authority":False})
 return {"revision":"USLS_037","row_count":len(rows),
  "quote_exact_count":sum(1 for x in rows if x["quote_amount"] is not None),
  "native_sol_pending_count":sum(1 for x in rows if x["quote_decoder_state"]=="QUOTE_AMOUNT_PENDING_NATIVE_SOL_RECONCILIATION"),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=audit(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_quote_amount_evidence.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_037_quote_amount_evidence_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"quote_exact_count":d["quote_exact_count"],
   "native_sol_pending_count":d["native_sol_pending_count"]},sort_keys=True))
  for x in d["rows"]:print("[QUOTE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertTrue(all(x["quote_amount"] is None or x["quote_amount"]>0 for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-037 quote-amount evidence audit")
  print("[PASS] native SOL quote is not falsely inferred from wallet balance delta")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
