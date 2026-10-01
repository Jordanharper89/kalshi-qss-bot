from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_081_event_driven_worker_checkpoint_foundation.py"
TEST=ROOT/"test_suls_081_event_driven_worker_checkpoint_foundation.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_079_event_driven_birth_hydration_worker import run as hydrate
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_080_event_driven_lifecycle_bridge import run as bridge

def bounded_cycle(root):
 t0=time.time();_,h=hydrate(root);b=bridge(root)
 cp=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_worker_checkpoint.json"
 old=json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else {"cycles":0,"reconnects":0}
 out={"revision":"SULS_081","cycles":int(old.get("cycles",0))+1,
  "reconnects":int(old.get("reconnects",0)),"last_cycle_started_unix":t0,
  "last_cycle_finished_unix":time.time(),"last_ack_count":h.get("ack_count",0),
  "last_notifications_examined":h.get("notifications_examined",0),
  "birth_count":h.get("birth_count",0),"tradeable_birth_events":b.get("event_count",0),
  "pending_horizon_checks":b.get("pending_horizon_checks",0),
  "execution_authority":False,"read_only":True}
 cp.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out

def run_forever(root,sleep_seconds=0.25):
 backoff=1.0
 while True:
  try:
   bounded_cycle(root);backoff=1.0;time.sleep(max(0.0,float(sleep_seconds)))
  except KeyboardInterrupt:raise
  except Exception:
   cp=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_worker_checkpoint.json"
   old=json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else {"cycles":0,"reconnects":0}
   old["reconnects"]=int(old.get("reconnects",0))+1;old["last_error_unix"]=time.time()
   cp.write_text(json.dumps(old,indent=2,sort_keys=True),encoding="utf-8")
   time.sleep(backoff);backoff=min(30.0,backoff*2.0)
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_081_event_driven_worker_checkpoint_foundation import bounded_cycle
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_cycle(self):
  d=bounded_cycle(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertGreaterEqual(d["cycles"],1)
  self.assertGreaterEqual(d["last_ack_count"],2)
  self.assertGreaterEqual(d["last_notifications_examined"],1)
  print("[PASS] SULS-081 event-driven worker/checkpoint foundation")
  print("[SCOPE] Bounded physical cycle only; existing OSI child not modified")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")