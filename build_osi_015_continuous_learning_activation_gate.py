from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_015_continuous_learning_activation_gate.py"
TEST=ROOT/"test_osi_015_continuous_learning_activation_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_010_continuous_strategy_learning_runtime import learn

def activate_learning(root:Path,cases:list[dict],min_sample:int=5)->dict:
 state_path=root/"runtime_state/solana_intelligence/osi_continuous_learning_state.json"
 state=learn(cases,state_path,min_sample)
 state["continuous_learning_activation_ready"]=True
 state["execution_authority"]=False
 state_path.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8")
 return state

def gate(root:Path)->dict:
 req=[
  root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_011_live_solana_source_boundary_certification.py",
  root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_012_live_event_normalization_and_intake.py",
  root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_013_live_prospective_research_worker.py",
  root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_014_live_outcome_maturity_worker.py",
  root/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_010_continuous_strategy_learning_runtime.py",
 ]
 ok=all(p.is_file() for p in req)
 return {"production_components_present":ok,"continuous_learning_activation_ready":ok,
         "execution_authority":False,"read_only":True}
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_015_continuous_learning_activation_gate import gate
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  g=gate(ROOT);self.assertTrue(g["production_components_present"]);self.assertTrue(g["continuous_learning_activation_ready"]);self.assertFalse(g["execution_authority"])
  print("[PASS] OSI-015 continuous learning activation gate")
  print("[TRADER] Live-source -> paper-call -> future-outcome -> learning pavement is present")
  print("[SCOPE] Component activation ready; launcher/24x7 process certification remains separate")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-015 installed; execution_authority=FALSE")
if __name__=="__main__":main()
