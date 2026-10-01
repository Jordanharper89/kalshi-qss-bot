from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_029_native_token_role_evidence_resolver.py"
TEST=ROOT/"test_suls_029_native_token_role_evidence_resolver.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def run(root):
 txd=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/exact_candidate_transaction.json").read_text(encoding="utf-8"))
 ixd=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/exact_instruction_accounts.json").read_text(encoding="utf-8"))
 ixmap={x["signature"]:x for x in ixd.get("rows",[])};rows=[]
 for t in txd.get("transactions",[]):
  e=t.get("envelope") or {};sig=e.get("signature");keys=(ixmap.get(sig) or {}).get("account_keys") or []
  pre=e.get("pre_token_balances") or [];post=e.get("post_token_balances") or [];balances=[]
  for b in post:
   idx=b.get("accountIndex") if isinstance(b,dict) else None
   if not isinstance(idx,int):continue
   pre_b=next((x for x in pre if isinstance(x,dict) and x.get("accountIndex")==idx),None)
   balances.append({"account_index":idx,"account":keys[idx] if idx<len(keys) else None,
    "mint":b.get("mint"),"owner":b.get("owner"),"program_id":b.get("programId"),
    "pre_ui":None if not pre_b else (pre_b.get("uiTokenAmount") or {}).get("uiAmountString"),
    "post_ui":(b.get("uiTokenAmount") or {}).get("uiAmountString")})
  target_accounts=sorted({a for x in (ixmap.get(sig) or {}).get("target_instructions",[]) for a in x.get("accounts",[]) if a})
  overlap=[b for b in balances if b.get("account") in target_accounts]
  rows.append({"signature":sig,"target_accounts":target_accounts,"target_token_balance_overlap":overlap,
   "distinct_mints":sorted({b["mint"] for b in overlap if b.get("mint")})})
 return {"revision":"SULS_029","rows":rows,"execution_authority":False}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_token_role_evidence.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_029_native_token_role_evidence_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_evidence(self):
  p,d=write(ROOT)
  for r in d["rows"]:
   print("[TARGET_ACCOUNTS]",len(r["target_accounts"]));print("[DISTINCT_MINTS]",json.dumps(r["distinct_mints"]))
   for x in r["target_token_balance_overlap"]:print("[TOKEN_ROLE_EVIDENCE]",json.dumps(x,sort_keys=True))
  if not any(r["target_token_balance_overlap"] for r in d["rows"]):self.fail("NO_TOKEN_BALANCE_ROLE_EVIDENCE")
  print("[PASS] SULS-029 native token-role evidence resolver")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")