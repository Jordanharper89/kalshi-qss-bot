from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime";MOD=SUB/"ssr_023_out_of_sample_rule_validation.py";TEST=ROOT/"test_ssr_023_out_of_sample_rule_validation.py"
MOD_TEXT=r"""from __future__ import annotations
import json,statistics
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_021_prospective_setup_feature_join import build as joined
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_022_time_ordered_rule_discovery import build as rules
OUT="runtime_state/solana_opportunities/profitability_runtime/oos_rule_validation.json"
def _hit(x,h):
 v=x["pre_outcome_features"].get(h["feature"])
 if h["op"]=="EQ":return v==h.get("value")
 if not isinstance(v,(int,float)):return False
 return float(v)>=h["threshold"] if h["op"]=="GE" else float(v)<h["threshold"]
def _m(rows):
 v=[x["gross_forward_return"] for x in rows];return {"n":len(v),"mean_gross_return":None if not v else sum(v)/len(v),"positive_frequency":None if not v else sum(x>0 for x in v)/len(v),"median_gross_return":None if not v else statistics.median(v)}
def build(root):
 j=joined(root);r=rules(root);fam={}
 for x in j["rows"]:fam.setdefault(x["family"],[]).append(x)
 out=[]
 for h in r["hypotheses"]:
  rows=sorted(fam[h["family"]],key=lambda x:x.get("freeze_unix") or 0);cut=max(3,int(len(rows)*.6));sel=[x for x in rows[cut:] if _hit(x,h)];m=_m(sel)
  out.append({**h,"validation":m,"validated_case_hashes":[x["freeze_hash"] for x in sel],"validation_pass":m["n"]>=2 and isinstance(m["mean_gross_return"],(int,float)) and m["mean_gross_return"]>0 and (m["positive_frequency"] or 0)>.5})
 out.sort(key=lambda x:(x["validation_pass"],x["validation"]["positive_frequency"] or -1,x["validation"]["mean_gross_return"] or -999,x["validation"]["n"]),reverse=True)
 return {"revision":"SSR_023","validated_rule_count":sum(x["validation_pass"] for x in out),"rule_count":len(out),"rules":out,"validation_semantics":"LATEST_40_PERCENT_HELD_OUT_FROM_RULE_DISCOVERY; MIN_2_MATCHES_FOR_INITIAL_PASS","statistical_sufficiency_claimed":False,"profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/OUT;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_023_out_of_sample_rule_validation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_validate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"rule_count":d["rule_count"],"validated_rule_count":d["validated_rule_count"]},sort_keys=True));self.assertFalse(d["statistical_sufficiency_claimed"]);self.assertFalse(d["execution_authority"]);print("[PASS] SSR-023 held-out rule validation")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8");print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")