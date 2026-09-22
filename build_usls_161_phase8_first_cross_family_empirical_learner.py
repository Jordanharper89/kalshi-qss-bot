from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_161_phase8_first_cross_family_empirical_learner.py"
TEST=ROOT/"test_usls_161_phase8_first_cross_family_empirical_learner.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase8_cross_family_nearest_neighbor_index.json"

def run(root):
 d=json.loads((Path(root)/SRC).read_text(encoding="utf-8"));rows=[]
 for x in d.get("indexed_cases",[]):
  vals=[n.get("forward_observational_return") for n in x.get("neighbors",[])
        if isinstance(n.get("forward_observational_return"),(int,float))]
  fams=sorted({n.get("family") for n in x.get("neighbors",[]) if n.get("family")})
  rows.append({"case_id":x["case_id"],"family":x["family"],
   "horizon_seconds":x["horizon_seconds"],"comparable_outcome_sample_size":len(vals),
   "comparable_family_count":len(fams),"comparable_families":fams,
   "raw_up_frequency":None if not vals else sum(v>0 for v in vals)/len(vals),
   "raw_down_frequency":None if not vals else sum(v<0 for v in vals)/len(vals),
   "mean_forward_observational_return":None if not vals else sum(vals)/len(vals),
   "calibrated_probability":None,"execution_authority":False})
 learnable=[x for x in rows if x["comparable_outcome_sample_size"]>=2]
 return {"revision":"USLS_161","case_count":len(rows),"learnable_case_count":len(learnable),
  "learned_cases":learnable,"all_cases":rows,
  "learning_semantics":"RAW_CROSS_FAMILY_EMPIRICAL_OUTCOMES_NOT_CALIBRATED_PROBABILITY",
  "next_boundary":"PHASE8_CROSS_FAMILY_LEARNING_CHECKPOINT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_first_cross_family_empirical_learner.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_161_phase8_first_cross_family_empirical_learner import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"case_count":d["case_count"],
   "learnable_case_count":d["learnable_case_count"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["case_count"],0)
  self.assertGreater(d["learnable_case_count"],0,"NO_CROSS_FAMILY_LEARNABLE_CASES")
  self.assertTrue(all(x["calibrated_probability"] is None for x in d["all_cases"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-161 first cross-family empirical learner")
  print("[PASS] comparable outcomes learned without converting raw frequency into calibrated probability")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
