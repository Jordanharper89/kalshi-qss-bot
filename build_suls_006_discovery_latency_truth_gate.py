from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_006_discovery_latency_truth_gate.py"
TEST=ROOT/"test_suls_006_discovery_latency_truth_gate.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
def gate(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_to_oracle_latency.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 mn=d.get("min_seconds");med=d.get("median_seconds")
 launch_grade=bool(mn is not None and mn<=5.0 and med is not None and med<=15.0)
 return {"revision":"SULS_006","measured":d.get("measured",0),"min_seconds":mn,"median_seconds":med,
 "launch_grade_birth_sensor":launch_grade,"classified_role":"PRIMARY_BIRTH_SENSOR" if launch_grade else "ENRICHMENT_DISCOVERY_ONLY",
 "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/discovery_latency_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_006_discovery_latency_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_truth(self):
  p,d=write(ROOT)
  print("[MIN_SECONDS]",d["min_seconds"]);print("[MEDIAN_SECONDS]",d["median_seconds"])
  print("[LAUNCH_GRADE_BIRTH_SENSOR]",d["launch_grade_birth_sensor"]);print("[CLASSIFIED_ROLE]",d["classified_role"])
  self.assertEqual(d["classified_role"],"ENRICHMENT_DISCOVERY_ONLY")
  print("[PASS] SULS-006 discovery latency truth gate")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name)