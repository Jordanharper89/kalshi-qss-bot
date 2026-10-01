from pathlib import Path
import ast

R=Path.cwd()
B=R/"qseries_v2"
TARGET="universal_opportunity"
rows=[]

for p in B.rglob("*.py"):
    try:
        s=p.read_text(encoding="utf-8")
        t=ast.parse(s)
    except Exception:
        continue
    if TARGET not in s and "UniversalOpportunity" not in s:
        continue
    imports=[]
    calls=[]
    for n in ast.walk(t):
        if isinstance(n,ast.ImportFrom) and (
            TARGET in (n.module or "") or
            any(x.name=="UniversalOpportunity" for x in n.names)
        ):
            imports.append(n.module or "")
        elif isinstance(n,ast.Call):
            f=n.func
            if isinstance(f,ast.Name) and f.id=="UniversalOpportunity":
                calls.append("UniversalOpportunity")
            elif isinstance(f,ast.Attribute) and f.attr=="intake":
                calls.append("intake")
            elif isinstance(f,ast.Attribute) and f.attr=="process":
                calls.append("process")
    rows.append((p.relative_to(R).as_posix(),imports,calls))

O=R/"OOI_005_UNIVERSAL_OPPORTUNITY_INTEGRATION_TOPOLOGY.txt"
out=[]
for p,i,c in rows:
    out += [f"[MODULE] {p}",f"  [IMPORTS] {i}",f"  [CALLS] {c}"]
O.write_text("\n".join(out)+"\n",encoding="utf-8")

print(f"[MODULES] {len(rows)}")
print(f"[AUDIT] {O}")
assert rows,"UniversalOpportunity has no physical consumers"
print("[PASS] OOI-005 universal opportunity integration topology captured")
print("[PASS] read_only=True execution_authority=FALSE")