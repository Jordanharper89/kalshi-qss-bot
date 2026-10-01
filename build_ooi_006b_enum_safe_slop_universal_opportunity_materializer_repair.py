from pathlib import Path
import ast
p=Path("qseries_v2/oracle_intelligence/universal_opportunity_model/universal_opportunity.py")
t=ast.parse(p.read_text(encoding="utf-8"))
enums={}
for n in t.body:
 if isinstance(n,ast.ClassDef):
  vals=[]
  for x in n.body:
   if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name):
    if isinstance(x.value,ast.Constant): vals.append((x.targets[0].id,x.value.value))
  if vals: enums[n.name]=vals
print("[UNIVERSAL_ENUMS]")
for k,v in enums.items(): print(k,v)
assert enums
print("[PASS] OOI-006B enum contract diagnostic")
print("[NEXT] use physical enum values; do not guess")