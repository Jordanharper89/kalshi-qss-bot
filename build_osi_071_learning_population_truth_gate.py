from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_071_learning_population_truth_gate.py"
TEST=ROOT/"test_osi_071_learning_population_truth_gate.py"
MOD_TEXT=r"""from __future__ import annotations
import json,collections
from pathlib import Path
def gate(root):
 p=root/"runtime_state/solana_opportunities/learning/empirical_cases.jsonl";rows=[]
 if p.is_file():
  rows=[json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
 by_h=collections.Counter(int(x["horizon_seconds"]) for x in rows)
 by_cls=collections.Counter(x["outcome_class"] for x in rows)
 formula_ready=len(rows)>=100 and all(by_h.get(h,0)>=20 for h in (5,15,30,60))
 return {"revision":"OSI_071","sample_size":len(rows),"by_horizon":dict(sorted(by_h.items())),
  "by_class":dict(sorted(by_cls.items())),"population_ingestion_ready":len(rows)>0,
  "formula_discovery_statistically_ready":formula_ready,
  "minimum_formula_sample_target":100,"minimum_per_short_horizon":20,
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/learning/population_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_071_learning_population_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[SAMPLE_SIZE]",d["sample_size"]);print("[BY_HORIZON]",json.dumps(d["by_horizon"],sort_keys=True));print("[BY_CLASS]",json.dumps(d["by_class"],sort_keys=True))
  print("[POPULATION_INGESTION_READY]",d["population_ingestion_ready"]);print("[FORMULA_DISCOVERY_STATISTICALLY_READY]",d["formula_discovery_statistically_ready"])
  if not d["population_ingestion_ready"]:self.fail("NO_REAL_EMPIRICAL_LEARNING_POPULATION")
  print("[PASS] OSI-071 learning population truth gate")
  print("[SCOPE] PASS does not claim enough samples for formula discovery")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*116);print(" OSI-071 LEARNING POPULATION TRUTH GATE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
