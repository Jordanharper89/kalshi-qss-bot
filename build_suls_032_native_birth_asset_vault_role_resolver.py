from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_032_native_birth_asset_vault_role_resolver.py"
TEST=ROOT/"test_suls_032_native_birth_asset_vault_role_resolver.py"

MOD_TEXT=r"""from __future__ import annotations
import json
WSOL="So11111111111111111111111111111111111111112"
def run(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 s=json.loads((b/"meteora_account_position_semantics.json").read_text(encoding="utf-8"))
 e=json.loads((b/"native_token_role_evidence.json").read_text(encoding="utf-8"))
 em={x["signature"]:x for x in e.get("rows",[])};rows=[]
 for r in s.get("rows",[]):
  sig=r["signature"];pos=set(r.get("position_nft_mints") or [])
  bal=(em.get(sig) or {}).get("target_token_balance_overlap") or []
  mints=sorted({x.get("mint") for x in bal if x.get("mint")})
  trade=[m for m in mints if m!=WSOL and m not in pos]
  quote=WSOL if WSOL in mints else None
  transfers=[x for x in r.get("transfers",[]) if x.get("mint") in set(trade+[quote] if quote else trade)]
  vaults={}
  for x in transfers:
   if x.get("mint") and x.get("destination"):
    vaults[x["mint"]]={"vault":x["destination"],"initial_amount":x.get("amount")}
  rows.append({"signature":sig,"trade_mint_candidates":trade,"quote_mint":quote,
   "position_nft_mints":sorted(pos),"vaults_by_mint":vaults,
   "roles_resolved":len(trade)==1 and quote is not None and trade[0] in vaults and quote in vaults})
 return {"revision":"SULS_032","rows":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_asset_vault_roles.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_032_native_birth_asset_vault_role_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_roles(self):
  p,d=write(ROOT)
  for r in d["rows"]:print("[ASSET_ROLES]",json.dumps(r,sort_keys=True))
  if not any(r["roles_resolved"] for r in d["rows"]):self.fail("BIRTH_ASSET_VAULT_ROLES_NOT_RESOLVED")
  print("[PASS] SULS-032 native birth asset/vault role resolver")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")