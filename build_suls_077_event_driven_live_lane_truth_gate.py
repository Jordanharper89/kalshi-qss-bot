from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_077_event_driven_live_lane_truth_gate.py"
TEST=ROOT/"test_suls_077_event_driven_live_lane_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 p=json.loads((b/"physical_confirmed_logs_subscription_probe.json").read_text(encoding="utf-8"))
 f=json.loads((b/"birth_log_notification_filter.json").read_text(encoding="utf-8"))
 return {"revision":"SULS_077","confirmed_websocket_connected":bool(p.get("connected")),
  "subscription_ack_count":int(p.get("ack_count",0)),"physical_notifications":int(p.get("notification_count",0)),
  "birth_log_candidates":int(f.get("birth_log_candidates",0)),
  "event_driven_live_lane_foundation_ready":bool(p.get("connected") and int(p.get("ack_count",0))>=2 and int(p.get("notification_count",0))>0),
  "signature_polling_role":"RESTART_BACKFILL_ONLY",
  "live_hydration_backlog_required":False,
  "production_24x7_active":False,"profitability_claimed":False,
  "next_required_boundary":"SULS_078_EVENT_DRIVEN_BIRTH_HYDRATION_AND_EXISTING_OSI_CHILD_INTEGRATION",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_live_lane_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_077_event_driven_live_lane_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["event_driven_live_lane_foundation_ready"]:self.fail("EVENT_DRIVEN_LIVE_LANE_NOT_READY")
  self.assertEqual(d["signature_polling_role"],"RESTART_BACKFILL_ONLY")
  self.assertFalse(d["production_24x7_active"]);self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-077 event-driven live-lane truth gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")