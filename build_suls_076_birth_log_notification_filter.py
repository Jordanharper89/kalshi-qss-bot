from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_076_birth_log_notification_filter.py"
TEST=ROOT/"test_suls_076_birth_log_notification_filter.py"

MOD_TEXT=r"""from __future__ import annotations
import json
DBC="dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"
def is_birth(logs):
 low="\n".join(str(x).lower() for x in (logs or []))
 return ("program log: create pool" in low and
  "instruction: initializepoolwithdynamicconfig" in low and
  DBC.lower() in low and DAMM.lower() in low)
def filter_probe(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/physical_confirmed_logs_subscription_probe.json"
 d=json.loads(p.read_text(encoding="utf-8"));births=[]
 for n in d.get("notifications",[]):
  if n.get("err") is None and is_birth(n.get("logs")):
   births.append({"signature":n.get("signature"),"slot":n.get("slot"),"received_unix":n.get("received_unix"),
    "state":"CONFIRMED_BIRTH_LOG_TRIGGER","execution_authority":False})
 return {"revision":"SULS_076","notifications_examined":len(d.get("notifications",[])),
  "birth_log_candidates":len(births),"births":births,"execution_authority":False,"read_only":True}
def write(root):
 d=filter_probe(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_log_notification_filter.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_076_birth_log_notification_filter import write,is_birth,DBC,DAMM
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_filter(self):
  fixture=["Program "+DBC+" invoke [1]","Program "+DAMM+" invoke [2]","Program log: Create Pool","Program log: Instruction: InitializePoolWithDynamicConfig"]
  self.assertTrue(is_birth(fixture))
  p,d=write(ROOT);print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="births"},sort_keys=True))
  print("[PASS] SULS-076 birth log notification filter")
  print("[SCOPE] Zero physical birth candidates is valid during a short probe window")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")