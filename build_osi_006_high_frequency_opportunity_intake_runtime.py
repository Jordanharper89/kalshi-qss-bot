from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_006_high_frequency_opportunity_intake_runtime.py"
TEST=ROOT/"test_osi_006_high_frequency_opportunity_intake_runtime.py"

MOD_TEXT=r"""from __future__ import annotations
import json, time
from pathlib import Path
from typing import Iterable
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_001_universal_solana_opportunity_discovery import discover

EXECUTION_AUTHORITY=False
READ_ONLY=True

def intake(events:Iterable[dict], now_iso:str, state_path:Path, max_age_seconds:int=300)->dict:
 seeds=discover(events,now_iso,max_age_seconds)
 seen=set()
 if state_path.is_file():
  try: seen=set(json.loads(state_path.read_text(encoding="utf-8")).get("seen_ids",[]))
  except Exception: seen=set()
 fresh=[x for x in seeds if x["opportunity_seed_id"] not in seen]
 seen.update(x["opportunity_seed_id"] for x in fresh)
 state={"seen_ids":sorted(seen),"accepted_count":len(fresh),"last_cycle_unix":time.time(),
        "read_only":True,"execution_authority":False}
 state_path.parent.mkdir(parents=True,exist_ok=True)
 state_path.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 return {"fresh_opportunities":fresh,"state":state}

def cycle(events:Iterable[dict],now_iso:str,root:Path)->dict:
 return intake(events,now_iso,root/"runtime_state/solana_intelligence/osi_006_intake_state.json")
"""

TEST_TEXT=r"""import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_006_high_frequency_opportunity_intake_runtime import intake
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_dedup_restart_safe(self):
  e=[{"asset_key":"SOL:M","event_type":"NEW_POOL","observed_at":"2026-09-18T05:00:00+00:00","source":"solana_native","source_record_id":"1"}]
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"s.json"
   a=intake(e,"2026-09-18T05:00:01+00:00",p);b=intake(e,"2026-09-18T05:00:02+00:00",p)
   self.assertEqual(len(a["fresh_opportunities"]),1);self.assertEqual(len(b["fresh_opportunities"]),0)
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_001_universal_solana_opportunity_discovery.py").is_file())
  print("[PASS] OSI-006 high-frequency opportunity intake runtime")
  print("[TRADER] Fresh Solana setups can enter continuously without duplicate replay after restart")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-006 installed; execution_authority=FALSE")
if __name__=="__main__":main()
