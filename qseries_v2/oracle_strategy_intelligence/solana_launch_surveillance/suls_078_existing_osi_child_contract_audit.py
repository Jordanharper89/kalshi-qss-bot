from __future__ import annotations
import json
TARGET="run_osi_solana_intelligence_live.py"

def audit(root):
 p=root/TARGET
 if not p.exists():
  return {"revision":"SULS_078","exists":False,"path":TARGET,"execution_authority":False,"read_only":True}
 src=p.read_text(encoding="utf-8",errors="ignore");lines=src.splitlines();hits=[]
 terms=("while","sleep","thread","async","solana","oad_","osi_","runtime_state","checkpoint","execution_authority","def main","if __name__")
 for i,line in enumerate(lines,1):
  if any(t.lower() in line.lower() for t in terms):
   hits.append({"line":i,"text":line[:600]})
 return {"revision":"SULS_078","exists":True,"path":TARGET,"line_count":len(lines),
  "hits":hits[:400],"imports_suls":"solana_launch_surveillance" in src,
  "execution_authority_false":"execution_authority" in src.lower() and "false" in src.lower(),
  "execution_authority":False,"read_only":True,
  "scope":"Read-only audit; existing OSI child unchanged"}

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/existing_osi_child_contract_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
