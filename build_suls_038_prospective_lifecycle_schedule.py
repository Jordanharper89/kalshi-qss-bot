from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_038_prospective_lifecycle_schedule.py"
TEST=ROOT/"test_suls_038_prospective_lifecycle_schedule.py"

MOD_TEXT=r"""from __future__ import annotations
import json
HORIZONS=(1,5,15,30,60,300,900)
def build(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for e in d.get("events",[]):
  bt=float(e["block_time"])
  for h in HORIZONS:
   rows.append({"event_id":e["event_id"],"signature":e["signature"],"horizon_seconds":h,
    "target_unix":bt+h,"state":"PENDING","execution_authority":False})
 return {"revision":"SULS_038","horizons":list(HORIZONS),"pending_count":len(rows),"pending":rows,
  "execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/prospective_lifecycle_schedule.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_038_prospective_lifecycle_schedule import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_schedule(self):
  p,d=write(ROOT);print("[HORIZONS]",d["horizons"]);print("[PENDING_COUNT]",d["pending_count"])
  self.assertEqual(d["horizons"],[1,5,15,30,60,300,900])
  if d["pending_count"]==0:self.fail("NO_PROSPECTIVE_LIFECYCLE_TARGETS")
  print("[PASS] SULS-038 prospective lifecycle schedule")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")