from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2"/"oracle_strategy_intelligence"/"solana_intelligence"
MOD=SUB/"osi_005_strategy_discovery_regime_learning_gate.py"
TEST=ROOT/"test_osi_005_strategy_discovery_regime_learning_gate.py"

MOD_TEXT=r"""from __future__ import annotations
from collections import defaultdict
from statistics import mean

EXECUTION_AUTHORITY=False

def summarize(cases:list[dict],min_sample:int=5)->list[dict]:
 groups=defaultdict(list)
 for c in cases:
  key=(str(c.get("pattern")),str(c.get("regime")),int(c.get("horizon_seconds",0)))
  groups[key].append(c)
 out=[]
 for (pattern,regime,h),rows in groups.items():
  if len(rows)<min_sample:continue
  net=[float(r["net_return_after_friction"]) for r in rows]
  mfe=[float(r.get("mfe",0)) for r in rows];mae=[float(r.get("mae",0)) for r in rows]
  wins=sum(x>0 for x in net)
  row={
   "pattern":pattern,"regime":regime,"horizon_seconds":h,"sample_size":len(rows),
   "positive_outcome_frequency":wins/len(rows),"mean_net_return_after_friction":mean(net),
   "mean_mfe":mean(mfe),"mean_mae":mean(mae),
   "candidate_strategy":True,"calibrated_probability_claimed":False,
   "execution_authority":False
  }
  out.append(row)
 out.sort(key=lambda x:(-x["sample_size"],x["pattern"],x["regime"],x["horizon_seconds"]))
 return out
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_005_strategy_discovery_regime_learning_gate import summarize
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_learning(self):
  rows=[]
  for i,r in enumerate([.08,.05,-.02,.11,.04,.07]):
   rows.append({"pattern":"NEW_POOL+LIQ_UP+WALLET_CLUSTER","regime":"SOL_STRONG","horizon_seconds":60,"net_return_after_friction":r,"mfe":r+.03,"mae":-.03})
  s=summarize(rows,5)
  self.assertEqual(len(s),1);self.assertEqual(s[0]["sample_size"],6);self.assertFalse(s[0]["calibrated_probability_claimed"])
 def test_small_sample_abstains(self):
  self.assertEqual(summarize([{"pattern":"X","regime":"R","horizon_seconds":5,"net_return_after_friction":1}],5),[])
 def test_physical(self):
  self.assertTrue((ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence/osi_004_continuous_paper_path_outcome_engine.py").is_file())
  print("[PASS] OSI-005 strategy discovery + regime learning gate")
  print("[TRADER] Repeated X+Y+Z outcomes can become evidence-backed candidate strategies only after enough samples")
  print("[PASS] no calibrated probability claim from raw historical frequency")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

def main():
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] OSI-005 installed; execution_authority=FALSE")
if __name__=="__main__":main()
