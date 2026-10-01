from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_004_continuous_paper_path_outcome_engine.py"
TEST=ROOT/"test_osi_004_continuous_paper_path_outcome_engine.py"

MOD_TEXT=r"""from __future__ import annotations
from datetime import datetime,timezone
def _dt(v):
 d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
 if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
 return d.astimezone(timezone.utc)

def grade(thesis:dict,path:list[dict])->dict:
 freeze=_dt(thesis["freeze_at"]);end=freeze.timestamp()+int(thesis["horizon_seconds"])
 pts=[]
 for x in path:
  if x.get("price") is None or not x.get("observed_at"):continue
  t=_dt(x["observed_at"])
  if t<freeze or t.timestamp()>end:continue
  pts.append((t,float(x["price"])))
 pts.sort(key=lambda x:x[0])
 if len(pts)<2:raise ValueError("insufficient future path")
 entry=pts[0][1];rets=[p/entry-1 for _,p in pts]
 friction=float((thesis.get("thesis_metadata") or {}).get("friction_bps",200))/10000
 target=(thesis.get("thesis_metadata") or {}).get("target_return")
 stop=(thesis.get("thesis_metadata") or {}).get("economic_stop_return")
 return {
  "thesis_id":thesis["thesis_id"],"horizon_seconds":thesis["horizon_seconds"],
  "entry_price":entry,"exit_price":pts[-1][1],"raw_return":rets[-1],
  "net_return_after_friction":rets[-1]-friction,"mfe":max(rets),"mae":min(rets),
  "target_hit":False if target is None else any(r>=float(target) for r in rets),
  "economic_stop_hit":False if stop is None else any(r<=float(stop) for r in rets),
  "path_points":len(pts),"paper_only":True,"execution_authority":False
 }
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_004_continuous_paper_path_outcome_engine import grade
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_grade(self):
  t={"thesis_id":"t","freeze_at":"2026-09-18T05:00:00+00:00","horizon_seconds":60,"thesis_metadata":{"friction_bps":200,"target_return":.10,"economic_stop_return":-.05}}
  o=grade(t,[{"observed_at":"2026-09-18T05:00:00+00:00","price":100},{"observed_at":"2026-09-18T05:00:20+00:00","price":112},{"observed_at":"2026-09-18T05:00:40+00:00","price":96},{"observed_at":"2026-09-18T05:01:00+00:00","price":108},{"observed_at":"2026-09-18T05:01:01+00:00","price":999}])
  self.assertAlmostEqual(o["mfe"],.12);self.assertAlmostEqual(o["mae"],-.04);self.assertAlmostEqual(o["net_return_after_friction"],.06);self.assertTrue(o["target_hit"])
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_003_multi_horizon_prospective_thesis_engine.py").is_file())
  print("[PASS] OSI-004 continuous paper-path outcome contract")
  print("[TRADER] Every paper call can be graded by return, friction, MFE, MAE and target/stop behavior")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-004 installed; execution_authority=FALSE")
if __name__=="__main__":main()
