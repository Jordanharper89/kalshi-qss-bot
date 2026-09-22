
from pathlib import Path
import ast
FILES=(
"qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
)
TOKENS=("CanonicalPersistenceQueryRequest","by_source_id","source_id","query","prefix","list",
        "distinct","backend","execute","fetch","read","observation","limit")
def audit(root=None):
 root=Path(root or Path.cwd()); out=[]
 for rel in FILES:
  p=root/rel; text=p.read_text(encoding="utf-8",errors="replace"); tree=ast.parse(text)
  funcs=[]
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    funcs.append({"name":n.name,"args":[a.arg for a in n.args.args],"line":n.lineno})
  hits=[]
  for i,line in enumerate(text.splitlines(),1):
   found=tuple(k for k in TOKENS if k.lower() in line.lower())
   if found:hits.append({"line":i,"tokens":found,"text":line.strip()})
  out.append({"file":rel,"functions":tuple(sorted(funcs,key=lambda x:x["line"])),"lineage":tuple(hits)})
 return {"files":tuple(out),"read_only":True,"execution_authority":False}
def print_audit(root=None):
 r=audit(root);print("[SSI-002F] CANONICAL SOURCE DISCOVERY CONTRACT AUDIT")
 for f in r["files"]:
  print("\\n[FILE]",f["file"]);print("[FUNCTIONS]",f["functions"])
  for h in f["lineage"]:print("[LINEAGE]",h)
 print("\\n[CONTRACT] read_only=True execution_authority=False");return r
