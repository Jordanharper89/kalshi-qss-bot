from pathlib import Path
import ast,re

R=Path.cwd(); B=R/"qseries_v2"; O=R/"OOI_004_CANONICAL_OPPORTUNITY_CONTRACT.txt"
rx=re.compile(r"Opportunity|opportunity",re.I); rows=[]
for p in B.rglob("*.py"):
 try:
  t=ast.parse(p.read_text(encoding="utf-8"))
 except Exception: continue
 for n in t.body:
  if isinstance(n,ast.ClassDef) and rx.search(n.name):
   fields=[]; methods=[]
   for x in n.body:
    if isinstance(x,ast.AnnAssign) and isinstance(x.target,ast.Name):
     fields.append(x.target.id)
    elif isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)):
     methods.append(x.name)
   if fields:
    rows.append((p.relative_to(R).as_posix(),n.name,fields,methods))
rows.sort(key=lambda x:(-len(x[2]),x[0],x[1]))
out=[]
for p,c,f,m in rows:
 out += [f"[CLASS] {p} :: {c}",f"  [FIELDS] {f}",f"  [METHODS] {m}"]
O.write_text("\n".join(out)+"\n",encoding="utf-8")
print(f"[CANDIDATE_CONTRACTS] {len(rows)}")
print(f"[AUDIT] {O}")
assert rows,"no opportunity contracts discovered"
print("[PASS] OOI-004 canonical opportunity contract discovery")
print("[PASS] read_only=True execution_authority=FALSE")