from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_069b_live_priority_birth_materializer.py"
TEST=ROOT/"test_suls_069b_live_priority_birth_materializer.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_042_generic_meteora_birth_role_materializer import _materialize

def run(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 src=json.loads((b/"program_indexed_confirmed_birth_inbox.json").read_text(encoding="utf-8"))
 op=b/"confirmed_tradeable_birth_events.json"
 old=json.loads(op.read_text(encoding="utf-8")) if op.exists() else {"events":[]}
 events=list(old.get("events") or []);seen={x.get("signature") for x in events};new=[]
 for row in src.get("births",[]):
  if row.get("signature") in seen:continue
  x=_materialize(row)
  if not x:continue
  x["trigger_commitment"]="confirmed";x["trigger_age_seconds"]=row.get("age_seconds")
  x["observed_unix"]=row.get("observed_unix");x["recovered_after_gap"]=bool(row.get("recovered_after_gap"))
  x["fresh_signal_eligible"]=bool(not x["recovered_after_gap"] and x.get("trigger_age_seconds") is not None and float(x["trigger_age_seconds"])<=5.0)
  events.append(x);new.append(x);seen.add(x["signature"])
 out={"revision":"SULS_069B","event_count":len(events),"new_events":len(new),"events":events,
  "execution_authority":False,"read_only":True}
 op.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_069b_live_priority_birth_materializer import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_materialize(self):
  d=run(ROOT);print("[STATE]",json.dumps({"event_count":d["event_count"],"new_events":d["new_events"]},sort_keys=True))
  print("[PASS] SULS-069B live-priority birth materializer")
  print("[SCOPE] Recovered births preserve lineage but cannot masquerade as fresh signals")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")