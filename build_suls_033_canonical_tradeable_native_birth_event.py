from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_033_canonical_tradeable_native_birth_event.py"
TEST=ROOT/"test_suls_033_canonical_tradeable_native_birth_event.py"

MOD_TEXT=r"""from __future__ import annotations
import json,hashlib
PROGRAM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"
def run(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 roles=json.loads((b/"native_birth_asset_vault_roles.json").read_text(encoding="utf-8"))
 tx=json.loads((b/"exact_candidate_transaction.json").read_text(encoding="utf-8"))
 tm={x.get("envelope",{}).get("signature"):x.get("envelope",{}) for x in tx.get("transactions",[])}
 out=[]
 for r in roles.get("rows",[]):
  if not r.get("roles_resolved"):continue
  sig=r["signature"];e=tm.get(sig) or {};trade=r["trade_mint_candidates"][0];quote=r["quote_mint"]
  raw=f"{sig}|{trade}|{quote}|{PROGRAM}"
  out.append({"event_id":"suls-birth-"+hashlib.sha256(raw.encode()).hexdigest(),
   "state":"DISCOVERED","signature":sig,"slot":e.get("slot"),"block_time":e.get("block_time"),
   "launcher_family":"METEORA_DAMM_V2","program_id":PROGRAM,
   "token_mint":trade,"quote_mint":quote,
   "token_vault":r["vaults_by_mint"][trade]["vault"],"quote_vault":r["vaults_by_mint"][quote]["vault"],
   "initial_token_amount":r["vaults_by_mint"][trade]["initial_amount"],
   "initial_quote_amount":r["vaults_by_mint"][quote]["initial_amount"],
   "execution_authority":False})
 return {"revision":"SULS_033","event_count":len(out),"events":out,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_033_canonical_tradeable_native_birth_event import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_event(self):
  p,d=write(ROOT);print("[EVENT_COUNT]",d["event_count"])
  for e in d["events"]:print("[TRADEABLE_BIRTH_EVENT]",json.dumps(e,sort_keys=True))
  if d["event_count"]==0:self.fail("NO_CANONICAL_NATIVE_BIRTH_EVENT")
  print("[PASS] SULS-033 canonical tradeable native birth event")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")