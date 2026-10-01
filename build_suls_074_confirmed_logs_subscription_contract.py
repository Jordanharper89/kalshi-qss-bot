from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_074_confirmed_logs_subscription_contract.py"
TEST=ROOT/"test_suls_074_confirmed_logs_subscription_contract.py"

MOD_TEXT=r"""from __future__ import annotations
import json
DBC="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"
PROGRAMS=(DBC,DAMM)

def contract(root):
 t=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/solana_rpc_transport_contract.json").read_text(encoding="utf-8"))
 subs=[]
 for i,pid in enumerate(PROGRAMS,1):
  subs.append({"jsonrpc":"2.0","id":i,"method":"logsSubscribe",
   "params":[{"mentions":[pid]},{"commitment":"confirmed"}]})
 return {"revision":"SULS_074","ws_url":t["derived_ws"],"programs":list(PROGRAMS),"subscriptions":subs,
  "birth_log_requirements":["Program log: Create Pool","Instruction: InitializePoolWithDynamicConfig"],
  "execution_authority":False,"read_only":True}
def write(root):
 d=contract(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/confirmed_logs_subscription_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_074_confirmed_logs_subscription_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(len(d["subscriptions"]),2)
  self.assertTrue(all(x["method"]=="logsSubscribe" for x in d["subscriptions"]))
  self.assertTrue(all(x["params"][1]["commitment"]=="confirmed" for x in d["subscriptions"]))
  print("[PASS] SULS-074 confirmed logsSubscribe contract")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")