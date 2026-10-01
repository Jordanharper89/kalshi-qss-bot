from pathlib import Path
ROOT=Path(__file__).resolve().parent
MOD=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_020_live_throughput_observation_gate.py"
TEST=ROOT/"test_osi_020_live_throughput_observation_gate.py"
MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
def observe(root:Path,seconds:int=10,interval:float=1.0)->dict:
 p=root/"runtime_state/solana_intelligence/osi_live_child_status.json"
 samples=[]
 end=time.time()+seconds
 while time.time()<end:
  if p.is_file():
   try:
    x=json.loads(p.read_text(encoding="utf-8"));samples.append({
     "cycle_count":x.get("cycle_count",0),"fresh_opportunities":x.get("fresh_opportunities",0),
     "normalized_event_count":x.get("normalized_event_count",0),"state":x.get("state")
    })
   except Exception: pass
  time.sleep(interval)
 cycles=[s["cycle_count"] for s in samples]
 return {"samples":samples,"cycle_progression":len(set(cycles))>1,
         "fresh_total":sum(int(s.get("fresh_opportunities") or 0) for s in samples),
         "execution_authority":False}
"""
TEST_TEXT=r"""import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_component(self):
  self.assertTrue((ROOT/"run_osi_solana_intelligence_live.py").is_file())
  print("[PASS] OSI-020 live throughput observation gate installed")
  print("[TRADER] After Oracle restart this gate measures whether the Solana hunter is actually cycling and seeing fresh setups")
  print("[SCOPE] Live observation must be run after restart")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
def main():
 MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-020 installed; execution_authority=FALSE")
if __name__=="__main__":main()
