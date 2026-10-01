from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_027_targeted_rule_freeze_filter import build as matched
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_031_targeted_rule_live_activation import ensure
def build(root):
 a=ensure(root);d=matched(root);base=set(a["baseline_matched_freeze_hashes"])
 new=[x for x in d["rows"] if x.get("freeze_hash") not in base and (x.get("freeze_unix") or 0)>=a["activation_unix"]]
 return {"revision":"SSR_032","activation_unix":a["activation_unix"],
  "baseline_match_count":a["baseline_matched_freeze_count"],"new_live_match_count":len(new),"new_live_matches":new,
  "execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/profitability_runtime/new_target_rule_matches.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
