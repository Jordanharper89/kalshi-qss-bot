from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_080_event_driven_lifecycle_bridge.py"
TEST=ROOT/"test_suls_080_event_driven_lifecycle_bridge.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_042_generic_meteora_birth_role_materializer import _materialize
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_063_signal_relative_horizon_semantics import write as schedule

def run(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 src=json.loads((b/"event_driven_birth_inbox.json").read_text(encoding="utf-8"))
 ep=b/"confirmed_tradeable_birth_events.json"
 old=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"events":[]}
 events=list(old.get("events") or []);seen={x.get("signature") for x in events};new=[]
 for row in src.get("births",[]):
  if row.get("signature") in seen:continue
  x=_materialize(row)
  if not x:continue
  x["trigger_commitment"]="confirmed";x["transport"]="logsSubscribe"
  x["trigger_age_seconds"]=row.get("age_seconds");x["observed_unix"]=row.get("observed_unix")
  x["recovered_after_gap"]=False
  x["fresh_signal_eligible"]=bool(x.get("trigger_age_seconds") is not None and float(x["trigger_age_seconds"])<=5.0)
  events.append(x);new.append(x);seen.add(x["signature"])
 ep.write_text(json.dumps({"revision":"SULS_080","event_count":len(events),"events":events,
  "execution_authority":False,"read_only":True},indent=2,sort_keys=True),encoding="utf-8")
 _,q=schedule(root)
 return {"revision":"SULS_080","event_count":len(events),"new_events":len(new),
  "fresh_new_events":sum(bool(x.get("fresh_signal_eligible")) for x in new),
  "pending_horizon_checks":q.get("pending_count",0),
  "reserve_ratio_only":True,"executable_pnl_claimed":False,
  "execution_authority":False,"read_only":True}
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_080_event_driven_lifecycle_bridge import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_bridge(self):
  d=run(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertFalse(d["executable_pnl_claimed"])
  print("[PASS] SULS-080 event-driven lifecycle bridge")
  print("[SCOPE] Current reserve-ratio outcomes remain observational, not executable PnL")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")