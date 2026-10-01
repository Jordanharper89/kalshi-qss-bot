from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_039_fresh_birth_lifecycle_admission_gate.py"
TEST=ROOT/"test_suls_039_fresh_birth_lifecycle_admission_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
MAX_AGE_SECONDS=5.0
def gate(root,now=None):
 now=float(time.time() if now is None else now)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
 d=json.loads(p.read_text(encoding="utf-8"));rows=[]
 for e in d.get("events",[]):
  age=max(0.0,now-float(e["block_time"]))
  rows.append({"event_id":e["event_id"],"age_seconds":age,
   "fresh_birth_admitted":age<=MAX_AGE_SECONDS,"max_age_seconds":MAX_AGE_SECONDS})
 return {"revision":"SULS_039","rows":rows,
  "fresh_birth_count":sum(x["fresh_birth_admitted"] for x in rows),
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/fresh_birth_lifecycle_admission.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_039_fresh_birth_lifecycle_admission_gate import gate,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[PHYSICAL_STATE]",json.dumps(d,sort_keys=True))
  src=ROOT/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
  original=src.read_text(encoding="utf-8")
  try:
   src.write_text(json.dumps({"events":[{"event_id":"x","block_time":100.0}]}),encoding="utf-8")
   f=gate(ROOT,103.0);self.assertEqual(f["fresh_birth_count"],1)
  finally:src.write_text(original,encoding="utf-8")
  print("[PASS] SULS-039 fresh-birth lifecycle admission gate")
  print("[SCOPE] Current historical event may be stale; prospective future births require <=5s admission")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")