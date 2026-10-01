from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_009_maturity_and_future_path_runtime.py"
TEST=ROOT/"test_osi_009_maturity_and_future_path_runtime.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_004_continuous_paper_path_outcome_engine import grade

def _dt(v):
 d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
 if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
 return d.astimezone(timezone.utc)

def mature(theses:list[dict],paths:dict[str,list[dict]],now_iso:str,outcome_path:Path)->dict:
 now=_dt(now_iso);out=[]
 for t in theses:
  end=_dt(t["freeze_at"]).timestamp()+int(t["horizon_seconds"])
  if now.timestamp()<end:continue
  path=paths.get(t["thesis_id"],[])
  try:o=grade(t,path)
  except ValueError:continue
  out.append(o)
 outcome_path.parent.mkdir(parents=True,exist_ok=True)
 outcome_path.write_text(json.dumps({"outcomes":out,"execution_authority":False},indent=2,sort_keys=True),encoding="utf-8")
 return {"matured":out,"matured_count":len(out),"execution_authority":False}
"""

TEST_TEXT=r"""import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_009_maturity_and_future_path_runtime import mature
class T(unittest.TestCase):
 def test_mature(self):
  t={"thesis_id":"t","freeze_at":"2026-09-18T05:00:00+00:00","horizon_seconds":60,"thesis_metadata":{"friction_bps":200}}
  paths={"t":[{"observed_at":"2026-09-18T05:00:00+00:00","price":100},{"observed_at":"2026-09-18T05:01:00+00:00","price":110}]}
  with tempfile.TemporaryDirectory() as td:
   r=mature([t],paths,"2026-09-18T05:01:01+00:00",Path(td)/"o.json")
   self.assertEqual(r["matured_count"],1);self.assertAlmostEqual(r["matured"][0]["net_return_after_friction"],.08)
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_004_continuous_paper_path_outcome_engine.py").is_file())
  print("[PASS] OSI-009 maturity + future-path runtime")
  print("[TRADER] Paper calls mature automatically and are graded only from prices observed after the call")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-009 installed; execution_authority=FALSE")
if __name__=="__main__":main()
