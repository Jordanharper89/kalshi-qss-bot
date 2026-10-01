from __future__ import annotations
import json
from pathlib import Path

FRI="runtime_state/solana_opportunities/solana_scanner/phase7_first_strict_executable_ready_rows.json"

def policy(root):
 root=Path(root);p=root/FRI
 d=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
 fam={}
 for x in d.get("ready_rows") or []:
  f=x.get("family")
  if f:fam[f]=fam.get(f,0)+1
 supported=sorted(fam,key=lambda f:fam[f],reverse=True)
 primary=supported[0] if supported else None
 return {"revision":"SSR_011","primary_money_hunt_family":primary,
  "physical_friction_family_counts":fam,
  "priority_rule":"FRICTION_SUPPORTED_FAMILIES_FIRST_THEN_UNSUPPORTED_OBSERVE_ONLY",
  "goal":"FIRST_PROSPECTIVE_OOS_X_PHYSICAL_FRICTION_NET_OUTCOME",
  "execution_authority":False,"read_only":True}

def write(root):
 d=policy(root);p=Path(root)/"runtime_state/solana_opportunities/profitability_runtime/money_hunt_priority.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
