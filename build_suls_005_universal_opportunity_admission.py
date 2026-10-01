from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_005_universal_opportunity_admission.py"
TEST=ROOT/"test_suls_005_universal_opportunity_admission.py"

MOD_TEXT=r"""from __future__ import annotations
import json,hashlib
from pathlib import Path

def admit(root):
 src=root/"runtime_state/solana_opportunities/launch_surveillance/physical_multi_launcher_discovery.json"
 d=json.loads(src.read_text(encoding="utf-8"));out=[]
 for e in d.get("events",[]):
  if not e.get("token_address") or not e.get("pair_address") or e.get("price_usd") is None:continue
  seed=f"{e['token_address']}|{e['pair_address']}|{e['oracle_observed_at']}".encode()
  oid="suls-"+hashlib.sha256(seed).hexdigest()
  out.append({"opportunity_id":oid,"token_address":e["token_address"],"pair_address":e["pair_address"],
   "launcher_family":e["launcher_family"],"dex_id":e.get("dex_id"),"state":"DISCOVERED",
   "first_observed_at":e["oracle_observed_at"],"pair_created_at_ms":e.get("pair_created_at_ms"),
   "price_usd":e.get("price_usd"),"market_cap":e.get("market_cap"),"fdv":e.get("fdv"),
   "liquidity_usd":e.get("liquidity_usd"),"volume_h24":e.get("volume_h24"),
   "buys_h24":e.get("buys_h24"),"sells_h24":e.get("sells_h24"),
   "source_id":e["source_id"],"execution_authority":False})
 return {"revision":"SULS_005","admitted_count":len(out),"opportunities":out,
  "admission_policy":"OBSERVE_ALL_VALID_POOLS_NO_MINIMUM_MC_OR_HOLDER_FILTER",
  "execution_authority":False}

def write(root):
 d=admit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/universal_opportunities.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_005_universal_opportunity_admission import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[ADMISSION_POLICY]",d["admission_policy"]);print("[ADMITTED_COUNT]",d["admitted_count"])
  for x in d["opportunities"][:20]:print("[OPPORTUNITY]",json.dumps(x,sort_keys=True))
  if d["admitted_count"]==0:self.fail("NO_SOLANA_OPPORTUNITIES_ADMITTED")
  print("[PASS] SULS-005 universal opportunity admission")
  print("[TRADER] Valid newborn/young pools are admitted for observation without excluding tiny market caps")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-005 UNIVERSAL OPPORTUNITY ADMISSION");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
