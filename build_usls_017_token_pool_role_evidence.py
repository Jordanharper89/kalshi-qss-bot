from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_017_token_pool_role_evidence.py"
TEST=ROOT/"test_usls_017_token_pool_role_evidence.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

KNOWN_QUOTES={
 "So11111111111111111111111111111111111111112":"WSOL",
 "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v":"USDC",
 "Es9vMFrzaCERmJfrF4H2FYD2XE8M6oEwErp2g5TjJ5J":"USDT"}

def roles(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 src=json.loads((base/"live_multifamily_transactions.json").read_text(encoding="utf-8"))
 rows=[]
 for r in src.get("rows") or []:
  tx=r.get("raw_transaction") or {};meta=tx.get("meta") or {}
  pre=meta.get("preTokenBalances") or [];post=meta.get("postTokenBalances") or []
  mints=sorted({x.get("mint") for x in pre+post if x.get("mint")})
  quotes=[m for m in mints if m in KNOWN_QUOTES]
  nonquotes=[m for m in mints if m not in KNOWN_QUOTES]
  owners=sorted({x.get("owner") for x in pre+post if x.get("owner")})
  rows.append({"signature":r.get("signature"),"families":r.get("families") or [],
   "all_mints":mints,"known_quote_mints":quotes,"candidate_token_mints":nonquotes,
   "token_account_owners":owners,"pre_token_balance_count":len(pre),
   "post_token_balance_count":len(post),"execution_authority":False})
 return {"revision":"USLS_017","row_count":len(rows),
  "token_candidate_rows":sum(1 for x in rows if x["candidate_token_mints"]),
  "quote_resolved_rows":sum(1 for x in rows if x["known_quote_mints"]),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=roles(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/token_pool_role_evidence.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_017_token_pool_role_evidence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("row_count","token_candidate_rows","quote_resolved_rows")},sort_keys=True))
  for r in d["rows"]:print("[ROLE]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(d["token_candidate_rows"],0)
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-017 token/quote role evidence extracted from live transactions")
  print("[SCOPE] candidate token roles only; pool identity is not guessed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
