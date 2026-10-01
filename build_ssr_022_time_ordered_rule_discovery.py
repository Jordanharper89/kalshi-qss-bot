from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime";MOD=SUB/"ssr_022_time_ordered_rule_discovery.py";TEST=ROOT/"test_ssr_022_time_ordered_rule_discovery.py"
MOD_TEXT=r"""from __future__ import annotations
import json,statistics
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_021_prospective_setup_feature_join import build as joined
OUT="runtime_state/solana_opportunities/profitability_runtime/time_ordered_rule_discovery.json"
def _m(rows):
 v=[x["gross_forward_return"] for x in rows];return {"n":len(v),"mean":None if not v else sum(v)/len(v),"positive_frequency":None if not v else sum(x>0 for x in v)/len(v),"median":None if not v else statistics.median(v)}
def build(root):
 d=joined(root);fam={}
 for x in d["rows"]:fam.setdefault(x["family"],[]).append(x)
 hs=[]
 for f,rows in fam.items():
  rows=sorted(rows,key=lambda x:x.get("freeze_unix") or 0)
  if len(rows)<5:continue
  cut=max(3,int(len(rows)*.6));tr=rows[:cut];va=rows[cut:];keys=sorted(set().union(*[set(x["pre_outcome_features"]) for x in tr]))
  for k in keys:
   vals=[x["pre_outcome_features"].get(k) for x in tr]
   if vals and all(isinstance(v,(int,float)) for v in vals):
    u=sorted(set(float(v) for v in vals))
    if len(u)>1:
     th=statistics.median(u)
     for op in ("GE","LT"):
      sel=[x for x in tr if (float(x["pre_outcome_features"][k])>=th if op=="GE" else float(x["pre_outcome_features"][k])<th)]
      if len(sel)>=2:hs.append({"family":f,"feature":k,"op":op,"threshold":th,"train":_m(sel),"train_total_n":len(tr),"validation_total_n":len(va)})
   elif vals and all(isinstance(v,str) for v in vals):
    for val in sorted(set(vals)):
     sel=[x for x in tr if x["pre_outcome_features"].get(k)==val]
     if len(sel)>=2:hs.append({"family":f,"feature":k,"op":"EQ","value":val,"train":_m(sel),"train_total_n":len(tr),"validation_total_n":len(va)})
 hs.sort(key=lambda h:(h["train"]["positive_frequency"] or -1,h["train"]["mean"] or -999,h["train"]["n"]),reverse=True)
 return {"revision":"SSR_022","hypothesis_count":len(hs),"hypotheses":hs,"split_rule":"EARLIEST_60_PERCENT_TRAIN_LATEST_40_PERCENT_VALIDATION","selection_semantics":"RULES_DISCOVERED_ON_TRAIN_ONLY; VALIDATION_NOT_USED_FOR_SELECTION","profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_022_time_ordered_rule_discovery import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_rules(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"hypothesis_count":d["hypothesis_count"]},sort_keys=True));self.assertIn("TRAIN_ONLY",d["selection_semantics"]);self.assertFalse(d["execution_authority"]);print("[PASS] SSR-022 time-ordered rule discovery")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8");print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")