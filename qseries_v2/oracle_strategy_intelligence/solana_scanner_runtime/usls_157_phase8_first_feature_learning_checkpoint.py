from __future__ import annotations
import json
from pathlib import Path

def _load(root,p):return json.loads((Path(root)/p).read_text(encoding="utf-8"))

def run(root):
 snap=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase8_leakage_safe_feature_snapshots.json")
 idx=_load(root,"runtime_state/solana_opportunities/solana_scanner/phase8_cross_launch_comparable_case_index.json")
 groups=idx.get("groups",[])
 learned=[g for g in groups if g.get("outcome_sample_size",0)>=2]
 cross=[g for g in learned if g.get("family_count",0)>=2]
 return {"revision":"USLS_157","phase":8,
  "snapshot_count":snap.get("snapshot_count",0),
  "comparable_group_count":len(groups),
  "learnable_group_count":len(learned),
  "cross_family_learnable_group_count":len(cross),
  "phase8_status":"IN_PROGRESS","phase8_physically_certified":False,
  "remaining_required_capability":
   "EXPAND_FEATURES_WITH_TRADE_FLOW_TRADER_LIQUIDITY_AND_EXECUTION_SIGNALS_THEN_PROSPECTIVE_OOS_FEATURE_OUTCOME_VALIDATION",
  "raw_frequency_only":True,"calibrated_probability_claimed":False,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_first_feature_learning_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
