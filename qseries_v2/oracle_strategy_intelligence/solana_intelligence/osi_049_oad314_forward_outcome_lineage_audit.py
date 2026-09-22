from __future__ import annotations
import json,re
from pathlib import Path
TARGETS=(
 "qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py",
 "qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py",
)
TOKENS=("outcome","forward","mfe","mae","return","horizon","price","path","json","jsonl","runtime","postgres","table","write","read")
def inspect(root):
 mods=[]
 for rel in TARGETS:
  p=root/rel
  if not p.is_file():continue
  hits=[]
  for n,line in enumerate(p.read_text(encoding="utf-8",errors="replace").splitlines(),1):
   if any(t in line.lower() for t in TOKENS):hits.append({"line":n,"text":line[:900]})
  mods.append({"module":rel,"matches":hits[:400]})
 return {"revision":"OSI_049","modules":mods,"module_count":len(mods),"execution_authority":False,"read_only":True}
def write(root):
 d=inspect(root);p=root/"runtime_state/solana_opportunities/oad314_forward_outcome_lineage.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
