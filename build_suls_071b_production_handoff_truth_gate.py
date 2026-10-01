from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_071b_production_handoff_truth_gate.py"
TEST=ROOT/"test_suls_071b_production_handoff_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 st=json.loads((b/"program_indexed_confirmed_state.json").read_text(encoding="utf-8"))
 cy=json.loads((b/"program_indexed_runtime_cycle.json").read_text(encoding="utf-8"))
 ep=b/"confirmed_tradeable_birth_events.json";op=b/"confirmed_horizon_outcomes.json"
 ev=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"event_count":0}
 out=json.loads(op.read_text(encoding="utf-8")) if op.exists() else {"outcome_count":0}
 fresh=sum(1 for x in ev.get("events",[]) if x.get("fresh_signal_eligible"))
 return {"revision":"SULS_071B","program_indexed_capture_ready":bool(st.get("last_cycle_unix") and len(st.get("anchors") or {})==2),
  "restart_backfill_ready":bool(st.get("restart_backfill_ready")),
  "live_priority_policy_ready":st.get("capture_policy")=="LIVE_NEWEST_FIRST_RECOVERY_BACKGROUND",
  "runtime_cycle_ready":bool(cy.get("capture")),"fresh_birth_physical_certified":fresh>0,
  "fresh_birth_count":fresh,"prospective_outcomes":int(out.get("outcome_count",0)),
  "existing_oracle_launcher_bound":False,"production_24x7_active":False,
  "profitability_learning_ready":bool(fresh>0 and int(out.get("outcome_count",0))>0),
  "profitability_claimed":False,
  "next_required_boundary":"SULS_072_EXISTING_ORACLE_PRODUCTION_LAUNCHER_INTEGRATION_CONTRACT_AUDIT",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/production_handoff_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_071b_production_handoff_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  for k in ("program_indexed_capture_ready","restart_backfill_ready","live_priority_policy_ready","runtime_cycle_ready"):
   if not d[k]:self.fail(k.upper()+"_FALSE")
  self.assertFalse(d["existing_oracle_launcher_bound"]);self.assertFalse(d["production_24x7_active"])
  self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-071B production handoff truth gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")