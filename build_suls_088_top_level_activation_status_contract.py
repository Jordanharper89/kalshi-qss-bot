from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_088_top_level_activation_status_contract.py"
TEST=ROOT/"test_suls_088_top_level_activation_status_contract.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
def inspect(root):
 osi=root/"runtime_state/solana_intelligence/osi_live_child_status.json"
 suls=root/"runtime_state/solana_opportunities/launch_surveillance/persistent_event_driven_runtime_status.json"
 od=json.loads(osi.read_text(encoding="utf-8")) if osi.exists() else {}
 sd=json.loads(suls.read_text(encoding="utf-8")) if suls.exists() else {}
 now=time.time()
 sh=sd.get("heartbeat_unix")
 return {"revision":"SULS_088","osi_status_found":osi.exists(),"suls_status_found":suls.exists(),
  "osi_status_keys":sorted(od.keys()),"suls_status_keys":sorted(sd.keys()),
  "suls_connected":bool(sd.get("connected")),"suls_ack_count":int(sd.get("ack_count",0)),
  "suls_notifications":int(sd.get("notifications",0)),
  "suls_heartbeat_age_seconds":None if sh is None else max(0.0,now-float(sh)),
  "production_24x7_active":False,"execution_authority":False,"read_only":True,
  "scope":"Status-contract discovery only; does not start or stop Oracle"}
def write(root):
 d=inspect(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/top_level_activation_status_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_088_top_level_activation_status_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["suls_status_found"])
  self.assertGreaterEqual(d["suls_ack_count"],2)
  print("[PASS] SULS-088 top-level activation/status contract")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*116);print(" SULS-088 TOP-LEVEL ACTIVATION / STATUS CONTRACT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()