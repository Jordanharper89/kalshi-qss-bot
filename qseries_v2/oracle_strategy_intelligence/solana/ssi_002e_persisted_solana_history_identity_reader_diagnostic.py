
from pathlib import Path
import ast
FILES=(
"qseries_v2/oracle_adapters/independent/oad_273_solana_pinned_pool_live_snapshot_persistence.py",
"qseries_v2/oracle_adapters/independent/oad_274_solana_multi_horizon_condition_windows.py",
)
TOKENS=("token_address","pair_address","observation_id","read_pinned_pool_history","persist",
        "postgres","sql","where","payload","pools","source_id","observation_type","limit")
def diagnose(root=None):
 root=Path(root or Path.cwd()); report=[]
 for rel in FILES:
  p=root/rel
  text=p.read_text(encoding="utf-8",errors="replace")
  tree=ast.parse(text); funcs=[]
  for n in ast.walk(tree):
   if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
    funcs.append({"name":n.name,"args":[a.arg for a in n.args.args],"line":n.lineno})
  hits=[]
  for i,line in enumerate(text.splitlines(),1):
   low=line.lower()
   found=tuple(k for k in TOKENS if k in low)
   if found: hits.append({"line":i,"tokens":found,"text":line.strip()})
  report.append({"file":rel,"functions":tuple(sorted(funcs,key=lambda x:x["line"])),"lineage":tuple(hits)})
 return {"files":tuple(report),"read_only":True,"execution_authority":False}
def print_diagnostic(root=None):
 r=diagnose(root)
 print("[SSI-002E] PERSISTED SOLANA HISTORY IDENTITY / READER DIAGNOSTIC")
 for f in r["files"]:
  print("\\n[FILE]",f["file"]);print("[FUNCTIONS]",f["functions"])
  for h in f["lineage"]: print("[LINEAGE]",h)
 print("\\n[CONTRACT] read_only=True execution_authority=False")
 return r
