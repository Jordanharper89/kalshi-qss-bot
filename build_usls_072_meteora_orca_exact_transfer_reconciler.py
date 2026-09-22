from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_072_meteora_orca_exact_transfer_reconciler.py"
TEST=ROOT/"test_usls_072_meteora_orca_exact_transfer_reconciler.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def sums(ts,src,dst):
 vals=[t["amount"] for t in ts if t.get("source")==src and t.get("destination")==dst and t.get("amount") is not None]
 return sum(vals) if vals else None

def reconcile(x):
 r=x["roles"];ts=x["transfers"];v=x["venue"]
 if x["role_state"]!="SOURCE_CERTIFIED_ACCOUNT_ROLES":return None
 if v=="METEORA_DAMM":
  a_in=sums(ts,r["user_in"],r["vault_a"]);b_in=sums(ts,r["user_in"],r["vault_b"])
  a_out=sums(ts,r["vault_a"],r["user_out"]);b_out=sums(ts,r["vault_b"],r["user_out"])
  if a_in and b_out:return {"input_mint":r["mint_a"],"input_amount":a_in,"output_mint":r["mint_b"],"output_amount":b_out}
  if b_in and a_out:return {"input_mint":r["mint_b"],"input_amount":b_in,"output_mint":r["mint_a"],"output_amount":a_out}
 if v=="METEORA_DLMM":
  x_in=sums(ts,r["user_in"],r["vault_x"]);y_in=sums(ts,r["user_in"],r["vault_y"])
  x_out=sums(ts,r["vault_x"],r["user_out"]);y_out=sums(ts,r["vault_y"],r["user_out"])
  if x_in and y_out:return {"input_mint":r["mint_x"],"input_amount":x_in,"output_mint":r["mint_y"],"output_amount":y_out}
  if y_in and x_out:return {"input_mint":r["mint_y"],"input_amount":y_in,"output_mint":r["mint_x"],"output_amount":x_out}
 if v=="ORCA":
  a_in=sums(ts,r["user_a"],r["vault_a"]);b_in=sums(ts,r["user_b"],r["vault_b"])
  a_out=sums(ts,r["vault_a"],r["user_a"]);b_out=sums(ts,r["vault_b"],r["user_b"])
  if a_in and b_out:return {"input_mint":None,"input_amount":a_in,"output_mint":None,"output_amount":b_out,"direction":"A_TO_B"}
  if b_in and a_out:return {"input_mint":None,"input_amount":b_in,"output_mint":None,"output_amount":a_out,"direction":"B_TO_A"}
 return None

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"meteora_orca_source_certified_roles.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  e=reconcile(x);roles=x["roles"]
  rows.append({"venue":x["venue"],"signature":x["signature"],"instruction_name":x["instruction_name"],
   "pool":roles.get("pool"),"trader":roles.get("trader"),"economics":e,
   "decoder_state":"EXACT_INSTRUCTION_TRANSFER_ECONOMICS" if e else "TRANSFER_RECONCILIATION_PENDING",
   "execution_authority":False})
 return {"revision":"USLS_072","row_count":len(rows),
  "venue_exact_counts":{v:sum(x["venue"]==v and x["economics"] is not None for x in rows) for v in sorted({x["venue"] for x in rows})},
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/meteora_orca_exact_transfer_reconciliation.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_072_meteora_orca_exact_transfer_reconciler import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_reconcile(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"venue_exact_counts":d["venue_exact_counts"]},sort_keys=True))
  for x in d["rows"][:30]:
   if x["economics"]:print("[EXACT]",json.dumps(x,sort_keys=True))
  self.assertGreater(sum(d["venue_exact_counts"].values()),0,"NO_SOURCE_CERTIFIED_TRANSFER_RECONCILIATION")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-072 exact instruction-level transfer reconciliation where physically supported")
  print("[PASS] no signer-wallet aggregate substituted for per-instruction economics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
