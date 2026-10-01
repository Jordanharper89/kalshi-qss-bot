from pathlib import Path
ROOT=Path(__file__).resolve().parent
MOD=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_020_live_throughput_observation_gate.py"
TEST=ROOT/"test_osi_020b_live_throughput_observation_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
def observe(root:Path,seconds:int=10,interval:float=1.0)->dict:
 p=root/"runtime_state/solana_intelligence/osi_live_child_status.json";samples=[];end=time.time()+seconds
 while time.time()<end:
  if p.is_file():
   try:
    x=json.loads(p.read_text(encoding="utf-8"));samples.append({"cycle_count":int(x.get("cycle_count") or 0),"fresh_opportunities":int(x.get("fresh_opportunities") or 0),"normalized_event_count":int(x.get("normalized_event_count") or 0),"state":x.get("state"),"error":x.get("error")})
   except Exception: pass
  time.sleep(interval)
 cycles=[x["cycle_count"] for x in samples]
 return {"sample_count":len(samples),"cycle_progression":len(set(cycles))>1,"min_cycle":min(cycles) if cycles else 0,"max_cycle":max(cycles) if cycles else 0,"fresh_total":sum(x["fresh_opportunities"] for x in samples),"normalized_event_total":sum(x["normalized_event_count"] for x in samples),"latest_state":samples[-1]["state"] if samples else None,"latest_error":samples[-1]["error"] if samples else None,"execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_020_live_throughput_observation_gate import observe
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_component_contract(self):
  self.assertTrue((ROOT/"run_osi_solana_intelligence_live.py").is_file())
  r=observe(ROOT,seconds=0,interval=.01);self.assertFalse(r["execution_authority"]);self.assertTrue(r["read_only"])
  print("[PASS] OSI-020B live throughput observation gate installed")
  print("[TRADER] This is the speedometer for the Solana hunter after Oracle restart")
  print("[SCOPE] Component certification only; live progression still requires physical observation")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-020B LIVE THROUGHPUT OBSERVATION GATE REBUILD");print("="*112)
 MOD.parent.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE");print("[SCOPE] Direct replacement for missing throughput gate")
if __name__=="__main__":main()
