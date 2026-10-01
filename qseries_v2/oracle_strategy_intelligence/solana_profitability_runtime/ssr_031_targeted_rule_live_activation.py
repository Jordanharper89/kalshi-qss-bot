from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_027_targeted_rule_freeze_filter import build as matched
REL="runtime_state/solana_opportunities/profitability_runtime/targeted_rule_live_activation.json"
def ensure(root):
 root=Path(root);p=root/REL
 if p.exists():return json.loads(p.read_text(encoding="utf-8"))
 d=matched(root);state={"revision":"SSR_031","activation_unix":time.time(),
  "baseline_matched_freeze_hashes":[x["freeze_hash"] for x in d["rows"] if x.get("freeze_hash")],
  "baseline_matched_freeze_count":d["matched_freeze_count"],
  "rule":"PUMP_SWAP_FIRST_PRICE_LT_4.326921673424848e-07",
  "execution_authority":False,"read_only":True}
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(state,indent=2,sort_keys=True),encoding="utf-8");return state
