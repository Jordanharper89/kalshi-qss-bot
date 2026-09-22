
from pathlib import Path
import ast,inspect
TOKENS=("by_observed_time_range","query_type","observed_from","observed_to","ORDER BY","LIMIT","ASC","DESC","fetch","query","cursor","offset")
def diagnose(root=None):
 root=Path(root or Path.cwd())
 from qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import _backend
 b=_backend(root);cls=type(b);out=[]
 print("[BACKEND_CLASS]",cls.__module__+"."+cls.__qualname__)
 print("[BACKEND_QUERY_SIGNATURE]",inspect.signature(b.query))
 files=["qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py"]
 src=inspect.getsourcefile(cls)
 if src:
  try: files.append(str(Path(src).resolve().relative_to(root.resolve())).replace(chr(92),"/"))
  except ValueError: pass
 for rel in dict.fromkeys(files):
  p=root/rel
  if not p.exists():continue
  text=p.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text);hits=[]
  funcs=[{"name":n.name,"args":[a.arg for a in n.args.args],"line":n.lineno} for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
  for i,line in enumerate(text.splitlines(),1):
   found=tuple(t for t in TOKENS if t.lower() in line.lower())
   if found:hits.append({"line":i,"tokens":found,"text":line.strip()})
  rec={"file":rel,"functions":tuple(sorted(funcs,key=lambda x:x["line"])),"hits":tuple(hits)};out.append(rec)
  print("\n[FILE]",rel);print("[FUNCTIONS]",rec["functions"])
  for h in hits:print("[LINEAGE]",h)
 r={"backend_class":cls.__module__+"."+cls.__qualname__,"files":tuple(out),"read_only":True,"execution_authority":False}
 print("\n[CONTRACT] read_only=True execution_authority=False");return r
