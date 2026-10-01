from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_093_fresh_birth_physical_capture_lifecycle_gate.py"
TEST=ROOT/"test_suls_093_fresh_birth_physical_capture_lifecycle_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time

MAX_FRESH_AGE=5.0
MAX_HEARTBEAT_AGE=30.0

def gate(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 ip=b/"event_driven_birth_inbox.json"
 ep=b/"confirmed_tradeable_birth_events.json"
 sp=b/"persistent_event_driven_runtime_status.json"

 inbox=json.loads(ip.read_text(encoding="utf-8")) if ip.exists() else {"births":[]}
 events=json.loads(ep.read_text(encoding="utf-8")) if ep.exists() else {"events":[]}
 status=json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}

 hb=status.get("heartbeat_unix")
 hb_age=None if hb is None else max(0.0,time.time()-float(hb))
 runtime_started=float(status.get("started_unix") or 0.0)

 fresh=[]
 for x in inbox.get("births",[]):
  age=x.get("age_seconds")
  obs=float(x.get("observed_unix") or 0.0)
  if (x.get("transport")=="logsSubscribe" and not x.get("recovered_after_gap")
      and age is not None and float(age)<=MAX_FRESH_AGE and obs>=runtime_started):
   fresh.append(x)

 materialized={x.get("signature"):x for x in events.get("events",[])}
 certified=[x for x in fresh if x.get("signature") in materialized]

 return {"revision":"SULS_093",
  "production_runtime_fresh":bool(status.get("connected") and int(status.get("ack_count",0))>=2
    and hb_age is not None and hb_age<=MAX_HEARTBEAT_AGE),
  "heartbeat_age_seconds":hb_age,
  "birth_inbox_count":len(inbox.get("births",[])),
  "fresh_birth_candidates":len(fresh),
  "fresh_materialized_births":len(certified),
  "fresh_signatures":[x.get("signature") for x in certified[-10:]],
  "fresh_birth_physical_certified":bool(certified),
  "lifecycle_materialization_certified":bool(certified),
  "profitability_learning_ready":False,
  "profitability_claimed":False,
  "next_required_boundary":"SULS_094_SIGNAL_RELATIVE_HORIZON_RETENTION_REPAIR_AND_PROSPECTIVE_SCHEDULING",
  "execution_authority":False,"read_only":True}

def write(root):
 d=gate(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/fresh_birth_physical_capture_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_093_fresh_birth_physical_capture_lifecycle_gate import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["production_runtime_fresh"]:
   self.fail("SULS_PRODUCTION_RUNTIME_NOT_FRESH")
  if not d["fresh_birth_physical_certified"]:
   self.fail("NO_FRESH_PROSPECTIVE_BIRTH_CAPTURED_YET")
  if not d["lifecycle_materialization_certified"]:
   self.fail("FRESH_BIRTH_NOT_MATERIALIZED")
  self.assertFalse(d["profitability_learning_ready"])
  self.assertFalse(d["profitability_claimed"])
  print("[PASS] SULS-093 fresh birth physical capture + lifecycle gate")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" SULS-093 FRESH BIRTH PHYSICAL CAPTURE + LIFECYCLE GATE")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 main()
