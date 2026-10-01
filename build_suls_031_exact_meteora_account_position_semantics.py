from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_031_exact_meteora_account_position_semantics.py"
TEST=ROOT/"test_suls_031_exact_meteora_account_position_semantics.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
WSOL="So11111111111111111111111111111111111111112"

def run(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/exact_candidate_transaction.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for t in d.get("transactions",[]):
  e=t.get("envelope") or {};raw=e.get("raw_transaction") or {};meta=raw.get("meta") or {}
  created=[];transfers=[];position_mints=set()
  for grp in meta.get("innerInstructions") or []:
   for ix in grp.get("instructions") or []:
    if not isinstance(ix,dict):continue
    parsed=ix.get("parsed") or {};info=parsed.get("info") or {};typ=parsed.get("type")
    if typ=="createAccount":
     created.append({"account":info.get("newAccount"),"owner_program":info.get("owner"),
      "space":info.get("space"),"lamports":info.get("lamports")})
    if typ in ("transferChecked","transfer"):
     transfers.append({"type":typ,"source":info.get("source"),"destination":info.get("destination"),
      "mint":info.get("mint"),"amount":(info.get("tokenAmount") or {}).get("uiAmountString")})
    if typ=="initializeTokenMetadata" and info.get("name")=="Meteora Position NFT":
     position_mints.add(info.get("mint"))
  rows.append({"signature":e.get("signature"),"created_accounts":created,"transfers":transfers,
   "position_nft_mints":sorted(x for x in position_mints if x),"wsol_mint":WSOL})
 return {"revision":"SULS_031","rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/meteora_account_position_semantics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_031_exact_meteora_account_position_semantics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_semantics(self):
  p,d=write(ROOT)
  for r in d["rows"]:
   print("[POSITION_NFT_MINTS]",json.dumps(r["position_nft_mints"]))
   print("[CREATED_ACCOUNTS]",json.dumps(r["created_accounts"],sort_keys=True))
   print("[TRANSFERS]",json.dumps(r["transfers"],sort_keys=True))
   if not r["position_nft_mints"]:self.fail("POSITION_NFT_NOT_IDENTIFIED")
   if not r["transfers"]:self.fail("NO_BIRTH_TRANSFERS")
  print("[PASS] SULS-031 exact Meteora account-position semantics")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")