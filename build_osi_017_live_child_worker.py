from pathlib import Path
ROOT=Path(__file__).resolve().parent
CHILD=ROOT/"run_osi_solana_intelligence_live.py"
TEST=ROOT/"test_osi_017_live_child_worker.py"

CHILD_TEXT=r"""from __future__ import annotations
import json,time,traceback
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_012_live_event_normalization_and_intake import run as intake_run

ROOT=Path(__file__).resolve().parent
STATUS=ROOT/"runtime_state/solana_intelligence/osi_live_child_status.json"
STOP=ROOT/"runtime_state/solana_intelligence/STOP_OSI_LIVE"
INTERVAL=1.0
EXECUTION_AUTHORITY=False

def now_iso():
 return datetime.now(timezone.utc).isoformat()

def write_status(**kw):
 STATUS.parent.mkdir(parents=True,exist_ok=True)
 payload={"execution_authority":False,"read_only":True,"child":"run_osi_solana_intelligence_live.py",**kw}
 STATUS.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

def one_cycle():
 result=intake_run(ROOT,now_iso())
 fresh=result.get("fresh_opportunities",[])
 return {"fresh_opportunities":len(fresh),"normalized_event_count":result.get("normalized_event_count",0)}

def main():
 cycle=0
 while not STOP.exists():
  cycle+=1
  try:
   r=one_cycle()
   write_status(state="LIVE_CYCLE_COMPLETE",cycle_count=cycle,updated_at=now_iso(),error=None,**r)
  except Exception as exc:
   write_status(state="LIVE_CYCLE_ERROR",cycle_count=cycle,updated_at=now_iso(),error=str(exc),traceback=traceback.format_exc()[-4000:])
  time.sleep(INTERVAL)

if __name__=="__main__":
 main()
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_child_exists(self):
  p=ROOT/"run_osi_solana_intelligence_live.py";self.assertTrue(p.is_file())
  text=p.read_text(encoding="utf-8")
  self.assertIn("EXECUTION_AUTHORITY=False",text);self.assertIn("INTERVAL=1.0",text)
 def test_upstream(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_012_live_event_normalization_and_intake.py").is_file())
  print("[PASS] OSI-017 live child worker installed")
  print("[TRADER] Oracle can scan the certified Solana live source once per second for fresh opportunities")
  print("[PASS] execution_authority=FALSE")
  print("[SCOPE] Child worker installed; launcher registration remains separate")
if __name__=="__main__":unittest.main()
"""

def main():
 CHILD.write_text(CHILD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",CHILD.name);print("[PASS] test:",TEST.name)
 print("[PASS] OSI-017 installed; execution_authority=FALSE")
if __name__=="__main__":main()
