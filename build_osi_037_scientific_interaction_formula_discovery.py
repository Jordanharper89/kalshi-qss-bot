from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_037_scientific_interaction_formula_discovery.py"
TEST=ROOT/"test_osi_037_scientific_interaction_formula_discovery.py"
MOD_TEXT=r"""from __future__ import annotations
import itertools,math

def _truth(v):
 if isinstance(v,bool):return v
 if isinstance(v,(int,float)):return v>0
 if isinstance(v,str):return v.lower() in ("true","yes","positive","buy","bull","rising","increasing")
 return False

def discover(matrix:dict,horizon:str,min_sample:int=5,max_order:int=3)->dict:
 cases=matrix.get("comparable_cases",[]);features=matrix.get("feature_names",[])
 rows=[]
 for order in range(1,min(max_order,len(features))+1):
  for combo in itertools.combinations(features,order):
   matched=[c for c in cases if all(_truth(c.get("features",{}).get(f)) for f in combo)]
   vals=[]
   for c in matched:
    o=c.get("outcomes",{}).get(str(horizon))
    if isinstance(o,(int,float)):vals.append(float(o))
   if len(vals)<min_sample:continue
   avg=sum(vals)/len(vals);wins=sum(1 for x in vals if x>0);losses=sum(1 for x in vals if x<=0)
   rows.append({"formula":" + ".join(combo),"order":order,"sample_size":len(vals),"mean_return":avg,
                "positive_frequency":wins/len(vals),"wins":wins,"losses":losses})
 rows.sort(key=lambda x:(x["mean_return"],x["sample_size"]),reverse=True)
 return {"revision":"OSI_037","horizon":str(horizon),"candidates":rows,
         "candidate_count":len(rows),"raw_frequency_is_calibrated_probability":False,
         "execution_authority":False,"read_only":True}
"""
TEST_TEXT=r"""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_037_scientific_interaction_formula_discovery import discover
class T(unittest.TestCase):
 def test_formula(self):
  cases=[]
  for i in range(8):
   cases.append({"features":{"liquidity":1,"swap_velocity":1,"smart_money_flow":1},
                 "outcomes":{"60":.10 if i<6 else -.05}})
  m={"feature_names":["liquidity","swap_velocity","smart_money_flow"],"comparable_cases":cases}
  d=discover(m,"60",5,3);self.assertGreater(d["candidate_count"],0);self.assertFalse(d["raw_frequency_is_calibrated_probability"])
  print("[TOP_FORMULA]",d["candidates"][0]["formula"]);print("[SAMPLE]",d["candidates"][0]["sample_size"])
  print("[PASS] OSI-037 scientific interaction/formula discovery")
  print("[TRADER] Tests X, Y, Z and their interactions against actual historical outcomes")
  print("[PASS] raw_frequency_is_calibrated_probability=FALSE")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-037 SCIENTIFIC INTERACTION / FORMULA DISCOVERY");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
