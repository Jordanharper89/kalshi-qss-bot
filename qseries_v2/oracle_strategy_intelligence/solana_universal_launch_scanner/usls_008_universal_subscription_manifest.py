from __future__ import annotations
import json
from pathlib import Path

def build(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 reg=json.loads((base/"verified_mainnet_program_registry.json").read_text(encoding="utf-8"))
 subs=[]
 for x in reg["programs"]:
  if not x.get("executable"):continue
  subs.append({"family":x["family"],"program_id":x["program_id"],
   "rpc_method":"logsSubscribe","filter":{"mentions":[x["program_id"]]},
   "commitment":"confirmed","retain_raw_transaction":True,
   "never_drop_unknown":True})
 return {"revision":"USLS_008","subscription_count":len(subs),"subscriptions":subs,
  "unknown_program_policy":"STRUCTURAL_DISCOVERY_RETAIN_AND_TRIAGE",
  "target_commitment":"confirmed","execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/subscription_manifest.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
