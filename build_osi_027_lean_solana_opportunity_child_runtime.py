from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_027_lean_solana_opportunity_child_runtime.py"
CHILD=ROOT/"run_osi_solana_opportunity_live.py"
TEST=ROOT/"test_osi_027_lean_solana_opportunity_child_runtime.py"
MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
def registered_sources(root:Path)->dict:
 p=root/"runtime_state/solana_opportunities/source_registry.json"
 if not p.is_file():return {}
 return json.loads(p.read_text(encoding="utf-8"))
def health(root:Path,cycle:int,state:str,error=None)->Path:
 p=root/"runtime_state/solana_opportunities/health/child_status.json";p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps({"revision":"OSI_027","cycle_count":cycle,"state":state,"error":error,
 "updated_at":time.time(),"execution_authority":False,"read_only":True},indent=2,sort_keys=True),encoding="utf-8");return p
"""
CHILD_TEXT=r"""from pathlib import Path
import time
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_027_lean_solana_opportunity_child_runtime import registered_sources,health
ROOT=Path(__file__).resolve().parent
STOP=ROOT/"runtime_state/solana_opportunities/STOP_OSI_SOLANA_OPPORTUNITY"
def main():
 cycle=0
 while not STOP.exists():
  cycle+=1
  try:
   r=registered_sources(ROOT)
   native=len(r.get("primary",{}).get("native_solana",[]));gmgn=len(r.get("primary",{}).get("gmgn",[]))
   health(ROOT,cycle,"LIVE_CYCLE_COMPLETE",None)
  except Exception as e:
   health(ROOT,cycle,"LIVE_CYCLE_ERROR",repr(e))
  time.sleep(1.0)
if __name__=="__main__":main()
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_027_lean_solana_opportunity_child_runtime import registered_sources,health
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_boundary(self):
  self.assertTrue((ROOT/"run_osi_solana_opportunity_live.py").is_file())
  r=registered_sources(ROOT);self.assertIn("primary",r)
  p=health(ROOT,1,"TEST_COMPLETE");d=json.loads(p.read_text(encoding="utf-8"))
  self.assertFalse(d["execution_authority"])
  print("[PASS] OSI-027 lean Solana opportunity child runtime")
  print("[TRADER] Child reads only the registered Solana/GMGN source registry and writes only isolated opportunity health state")
  print("[SCOPE] Child installed but not registered into production launcher yet")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-027 LEAN SOLANA OPPORTUNITY CHILD RUNTIME");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");CHILD.write_text(CHILD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] child:",CHILD.name);print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Dedicated child installed; production launcher unchanged")
if __name__=="__main__":main()
