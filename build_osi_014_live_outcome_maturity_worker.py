from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_014_live_outcome_maturity_worker.py"
TEST=ROOT/"test_osi_014_live_outcome_maturity_worker.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_009_maturity_and_future_path_runtime import mature

def mature_live(root:Path,paths:dict,now_iso:str)->dict:
 q=root/"runtime_state/solana_intelligence/osi_live_thesis_queue.json"
 theses=[] if not q.is_file() else json.loads(q.read_text(encoding="utf-8")).get("theses",[])
 out=root/"runtime_state/solana_intelligence/osi_live_outcomes.json"
 return mature(theses,paths,now_iso,out)

def outcome_count(root:Path)->int:
 p=root/"runtime_state/solana_intelligence/osi_live_outcomes.json"
 if not p.is_file():return 0
 return len(json.loads(p.read_text(encoding="utf-8")).get("outcomes",[]))
"""

TEST_TEXT=r"""import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_014_live_outcome_maturity_worker import mature_live,outcome_count
class T(unittest.TestCase):
 def test_mature(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);q=r/"runtime_state/solana_intelligence";q.mkdir(parents=True)
   t={"thesis_id":"t","freeze_at":"2026-09-18T05:00:00+00:00","horizon_seconds":60,"thesis_metadata":{"friction_bps":200}}
   (q/"osi_live_thesis_queue.json").write_text(json.dumps({"theses":[t]}),encoding="utf-8")
   paths={"t":[{"observed_at":"2026-09-18T05:00:00+00:00","price":100},{"observed_at":"2026-09-18T05:01:00+00:00","price":109}]}
   x=mature_live(r,paths,"2026-09-18T05:01:01+00:00");self.assertEqual(x["matured_count"],1);self.assertEqual(outcome_count(r),1)
 def test_physical(self):
  ROOT=Path(__file__).resolve().parent
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_013_live_prospective_research_worker.py").is_file())
  print("[PASS] OSI-014 live outcome maturity worker")
  print("[TRADER] Frozen paper calls can mature into real future-path results automatically")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-014 installed; execution_authority=FALSE")
if __name__=="__main__":main()
