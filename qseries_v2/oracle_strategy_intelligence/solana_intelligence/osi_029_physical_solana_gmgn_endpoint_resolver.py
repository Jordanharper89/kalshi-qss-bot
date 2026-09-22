from __future__ import annotations
import ast,json,re
from pathlib import Path

SOURCE_REGISTRY="runtime_state/solana_opportunities/source_registry.json"
RUNTIME_ROOTS=("runtime","runtime_state")

def _string_literals(path:Path)->list[str]:
 out=[]
 try:
  tree=ast.parse(path.read_text(encoding="utf-8",errors="replace"))
  for node in ast.walk(tree):
   if isinstance(node,ast.Constant) and isinstance(node.value,str):
    v=node.value.strip()
    if any(x in v.lower() for x in ("runtime","json","jsonl","sqlite","db","postgres","pool","mint","swap","wallet","gmgn","solana")):
     out.append(v)
 except Exception:
  pass
 return out

def _runtime_files(root:Path)->list[Path]:
 out=[]
 for base in RUNTIME_ROOTS:
  p=root/base
  if p.exists():
   out.extend(x for x in p.rglob("*") if x.is_file())
 return out

def resolve(root:Path)->dict:
 reg_path=root/SOURCE_REGISTRY
 if not reg_path.is_file():raise RuntimeError("Missing OSI-026 source registry")
 reg=json.loads(reg_path.read_text(encoding="utf-8"))
 files=_runtime_files(root)
 native=[];gmgn=[]
 def inspect(entry,kind):
  rel=entry.get("module","");p=root/rel
  lits=_string_literals(p) if p.is_file() else []
  matches=[]
  for f in files:
   fr=str(f.relative_to(root)).replace("\\","/").lower()
   if kind=="NATIVE_SOLANA":
    if any(t in fr for t in ("solana","pool","mint","swap","token")):matches.append(f)
   else:
    if "gmgn" in fr:matches.append(f)
  return {"module":rel,"literals":lits[:100],
          "runtime_matches":[str(x.relative_to(root)) for x in matches[:200]]}
 for x in reg.get("primary",{}).get("native_solana",[]):native.append(inspect(x,"NATIVE_SOLANA"))
 for x in reg.get("primary",{}).get("gmgn",[]):gmgn.append(inspect(x,"GMGN"))
 physical_native=sorted({p for x in native for p in x["runtime_matches"]})
 physical_gmgn=sorted({p for x in gmgn for p in x["runtime_matches"]})
 return {"revision":"OSI_029","native_modules":native,"gmgn_modules":gmgn,
  "physical_native_files":physical_native,"physical_gmgn_files":physical_gmgn,
  "native_file_count":len(physical_native),"gmgn_file_count":len(physical_gmgn),
  "execution_authority":False,"read_only":True}

def write(root:Path)->Path:
 d=resolve(root);p=root/"runtime_state/solana_opportunities/physical_source_endpoints.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
