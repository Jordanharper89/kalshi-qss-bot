from __future__ import annotations
import json
CANDIDATES=("run_oracle_live.py","run_oracle_LIVE.py")

def audit(root):
 rows=[]
 for name in CANDIDATES:
  p=root/name
  if not p.exists():continue
  src=p.read_text(encoding="utf-8",errors="ignore");hits=[]
  terms=("solana","gmgn","crypto_learning","fast_lane","inventory","reasoning","learning","thread","worker","daemon","start(")
  for i,line in enumerate(src.splitlines(),1):
   if any(t.lower() in line.lower() for t in terms):
    hits.append({"line":i,"text":line[:500]})
  rows.append({"path":name,"line_count":len(src.splitlines()),"hits":hits[:250],
    "imports_solana_launch_surveillance":"solana_launch_surveillance" in src,
    "mentions_execution_authority_false":"execution_authority" in src.lower() and "false" in src.lower()})
 return {"revision":"SULS_072","launcher_count":len(rows),"launchers":rows,
  "execution_authority":False,"read_only":True,
  "scope":"Read-only contract audit only; production launcher unchanged"}

def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/existing_oracle_launcher_contract_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
