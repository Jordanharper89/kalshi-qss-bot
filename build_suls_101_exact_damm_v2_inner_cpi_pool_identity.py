from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_101_exact_damm_v2_inner_cpi_pool_identity.py"
TEST=ROOT/"test_suls_101_exact_damm_v2_inner_cpi_pool_identity.py"

MOD_TEXT=r'''from __future__ import annotations
import json

DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"

def certify(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json"
 births=list(json.loads(p.read_text(encoding="utf-8")).get("births") or [])
 if not births:raise RuntimeError("NO_BIRTHS")
 for b in reversed(births):
  raw=((b.get("envelope") or {}).get("raw_transaction") or {})
  msg=(raw.get("transaction") or {}).get("message") or {}
  meta=raw.get("meta") or {};keys=msg.get("accountKeys") or []
  def key(x):
   if isinstance(x,str):return x
   if isinstance(x,int) and 0<=x<len(keys):
    v=keys[x];return v.get("pubkey") if isinstance(v,dict) else v
   return None
  candidates=[]
  for grp in meta.get("innerInstructions") or []:
   for ix in grp.get("instructions") or []:
    if not isinstance(ix,dict):continue
    program=ix.get("programId") or key(ix.get("programIdIndex"))
    if program!=DAMM:continue
    ac=[key(x) for x in ix.get("accounts") or []]
    if len(ac)>=21:
     candidates.append({"outer_index":grp.get("index"),"accounts":ac,"data":ix.get("data")})
  if not candidates:continue
  c=max(candidates,key=lambda x:len(x["accounts"]));a=c["accounts"]
  return {"revision":"SULS_101","signature":b.get("signature"),
   "outer_index":c["outer_index"],"account_count":len(a),
   "creator":a[0],"position_nft_mint":a[1],"position_nft_account":a[2],
   "payer":a[3],"pool_creator_authority":a[4],"config":a[5],
   "pool_authority":a[6],"pool_address":a[7],"position":a[8],
   "token_a_mint":a[9],"token_b_mint":a[10],
   "token_a_vault":a[11],"token_b_vault":a[12],
   "payer_token_a":a[13],"payer_token_b":a[14],
   "accounts":a,"execution_authority":False,"read_only":True}
 raise RuntimeError("NO_DAMM_V2_21_ACCOUNT_INNER_CPI_FOUND")

def write(root):
 d=certify(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/damm_v2_pool_identity_certification.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
'''

TEST_TEXT=r'''import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_101_exact_damm_v2_inner_cpi_pool_identity import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_identity(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="accounts"},sort_keys=True))
  print("[ACCOUNTS]",json.dumps(d["accounts"],indent=2))
  self.assertGreaterEqual(d["account_count"],21)
  self.assertTrue(d["pool_address"])
  self.assertTrue(d["token_a_mint"])
  self.assertTrue(d["token_b_mint"])
  self.assertTrue(d["token_a_vault"])
  self.assertTrue(d["token_b_vault"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] SULS-101 exact DAMM V2 inner-CPI pool identity certification")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
'''

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")