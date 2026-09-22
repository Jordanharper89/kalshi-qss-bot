from __future__ import annotations
import json
def gate(root):
 rows=[]
 for name in ("run_oracle_live.py","run_oracle_LIVE.py"):
  p=root/name
  if not p.exists():continue
  s=p.read_text(encoding="utf-8",errors="ignore")
  rows.append({"path":name,"registered":"run_osi_solana_intelligence_live.py" in s,
   "suls_direct_registration":"solana_launch_surveillance" in s})
 return {"revision":"SULS_089","launchers":rows,
  "osi_registered_all":bool(rows) and all(x["registered"] for x in rows),
  "no_direct_suls_registration":bool(rows) and all(not x["suls_direct_registration"] for x in rows),
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/top_level_osi_registration_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
