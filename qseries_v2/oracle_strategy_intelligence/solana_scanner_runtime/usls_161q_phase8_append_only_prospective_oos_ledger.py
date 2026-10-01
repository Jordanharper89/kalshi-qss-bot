from __future__ import annotations
import json
from pathlib import Path
SRC="runtime_state/solana_opportunities/solana_scanner/phase8_bidirectional_frozen_pair_outcomes.json"
DST="runtime_state/solana_opportunities/solana_scanner/phase8_prospective_oos_ledger.json"

def run(root):
 root=Path(root);src=json.loads((root/SRC).read_text(encoding="utf-8"))
 old={"cases":[]} if not (root/DST).exists() else json.loads((root/DST).read_text(encoding="utf-8"))
 idx={(x.get("freeze_hash"),x.get("later_trade_signature")):x for x in old.get("cases",[])}
 before=len(idx)
 for x in src.get("cases",[]):
  k=(x.get("freeze_hash"),x.get("later_trade_signature"))
  if None not in k:idx.setdefault(k,x)
 cases=sorted(idx.values(),key=lambda x:(x.get("freeze_unix") or 0,x.get("later_observed_unix") or 0))
 fam={}
 for x in cases:fam[x["family"]]=fam.get(x["family"],0)+1
 return {"revision":"USLS_161Q","case_count":len(cases),"new_case_count":len(cases)-before,
  "family_case_counts":fam,"cases":cases,"dedupe_key":"FREEZE_HASH_PLUS_LATER_TRADE_SIGNATURE",
  "future_leakage":"FORBIDDEN","next_boundary":"PROSPECTIVE_FEATURE_OUTCOME_EMPIRICAL_LEARNER",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=Path(root)/DST;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8");return p,d
