from __future__ import annotations
import json,re
from pathlib import Path
B58=re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
KEYS=("program_id","programId","program","owner","dex_id","pumpfun","pumpswap","raydium","meteora","moonshot","stonk","bonk","orca")
def audit(root):
 bases=[root/"qseries_v2/oracle_adapters/independent",root/"runtime_state/solana_opportunities"]
 rows=[]
 for base in bases:
  if not base.exists():continue
  pats=("*.py","*.json","*.jsonl")
  for pat in pats:
   for p in base.rglob(pat):
    try:text=p.read_text(encoding="utf-8",errors="ignore")
    except Exception:continue
    if not any(k.lower() in text.lower() for k in KEYS):continue
    addrs=sorted(set(B58.findall(text)))[:30]
    labels=sorted({k for k in KEYS if k.lower() in text.lower()})
    if addrs or labels:rows.append({"file":str(p.relative_to(root)),"labels":labels,"base58_candidates":addrs})
 return {"revision":"SULS_008","evidence_files":len(rows),"rows":rows[:200],"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/program_identity_evidence_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
