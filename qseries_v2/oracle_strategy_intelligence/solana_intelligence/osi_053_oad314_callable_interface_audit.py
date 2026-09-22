from __future__ import annotations
import ast,inspect,json
from pathlib import Path
TARGET="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
def audit(root):
 p=root/TARGET
 if not p.is_file():raise RuntimeError("Missing OAD-314")
 text=p.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text)
 funcs=[]
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
   args=[a.arg for a in n.args.args]
   funcs.append({"name":n.name,"line":n.lineno,"args":args})
 imports=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.ImportFrom):imports.append({"module":n.module,"names":[x.name for x in n.names]})
  elif isinstance(n,ast.Import):imports.extend({"module":x.name,"names":[]} for x in n.names)
 returns=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Return):returns.append({"line":n.lineno,"text":ast.get_source_segment(text,n.value)[:1000] if n.value else None})
 return {"revision":"OSI_053","module":TARGET,"functions":funcs,"imports":imports[:200],"returns":returns[:200],"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/oad314_callable_interface.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
