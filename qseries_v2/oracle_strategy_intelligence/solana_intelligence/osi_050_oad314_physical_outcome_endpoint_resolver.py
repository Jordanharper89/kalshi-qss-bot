from __future__ import annotations
import ast,json
from pathlib import Path
TARGET="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
def resolve(root):
 p=root/TARGET
 if not p.is_file():raise RuntimeError("Missing certified OAD-314 module")
 vals=[]
 try:
  tree=ast.parse(p.read_text(encoding="utf-8",errors="replace"))
  for n in ast.walk(tree):
   if isinstance(n,ast.Constant) and isinstance(n.value,str):
    s=n.value.strip().replace("\\","/")
    if any(x in s.lower() for x in ("runtime","json","jsonl","sqlite","db","postgres","outcome","forward","path")):vals.append(s)
 except Exception:pass
 files=[]
 for base_name in ("runtime","runtime_state"):
  base=root/base_name
  if not base.exists():continue
  for f in base.rglob("*"):
   if not f.is_file():continue
   rel=str(f.relative_to(root)).replace("\\","/")
   low=rel.lower()
   if any(v.lower().lstrip("./")==low or ("/" in v and low.endswith(v.lower().lstrip("./"))) for v in vals):files.append(rel)
 return {"revision":"OSI_050","module":TARGET,"string_literals":vals[:300],"physical_files":sorted(set(files)),"physical_file_count":len(set(files)),"execution_authority":False,"read_only":True}
def write(root):
 d=resolve(root);p=root/"runtime_state/solana_opportunities/oad314_physical_outcome_endpoints.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
