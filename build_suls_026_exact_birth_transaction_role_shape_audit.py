from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_026_exact_birth_transaction_role_shape_audit.py"
TEST=ROOT/"test_suls_026_exact_birth_transaction_role_shape_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def audit(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_candidate_transaction.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for t in d.get("transactions",[]):
  e=t.get("envelope") or {}
  raw=e.get("raw_transaction") or {}
  tx=raw.get("transaction") or {};msg=tx.get("message") or {};meta=raw.get("meta") or {}
  rows.append({
   "slot":e.get("slot"),"signature":e.get("signature"),
   "account_keys":e.get("account_keys") or msg.get("accountKeys") or [],
   "outer_instructions":e.get("instructions") or msg.get("instructions") or [],
   "inner_instructions":e.get("inner_instructions") or meta.get("innerInstructions") or [],
   "pre_token_balances":e.get("pre_token_balances") or meta.get("preTokenBalances") or [],
   "post_token_balances":e.get("post_token_balances") or meta.get("postTokenBalances") or [],
  })
 return {"revision":"SULS_026","rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_birth_role_shape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_026_exact_birth_transaction_role_shape_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);self.assertTrue(d["rows"])
  for r in d["rows"]:
   print("[ACCOUNT_KEYS]",len(r["account_keys"]))
   print("[OUTER_INSTRUCTIONS]",len(r["outer_instructions"]))
   print("[INNER_GROUPS]",len(r["inner_instructions"]))
   print("[PRE_TOKEN_BALANCES]",len(r["pre_token_balances"]))
   print("[POST_TOKEN_BALANCES]",len(r["post_token_balances"]))
   print("[ROLE_SHAPE]",json.dumps(r,sort_keys=True)[:12000])
  print("[PASS] SULS-026 exact birth transaction role-shape audit")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")