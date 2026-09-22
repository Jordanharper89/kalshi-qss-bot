from pathlib import Path
import ast

p=Path.cwd()/"qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py"
src=p.read_text(encoding="utf-8")
tree=ast.parse(src)

fn=next(
    n for n in tree.body
    if isinstance(n,ast.FunctionDef) and n.name=="canonicalize_expansion_observation"
)

print("[FUNCTION]",ast.unparse(fn).split("\n")[0])
print("[BODY]")
print(ast.unparse(fn))

attrs=sorted({
    n.attr for n in ast.walk(fn)
    if isinstance(n,ast.Attribute)
    and isinstance(n.value,ast.Name)
    and n.value.id=="x"
})
print("[X_ATTRIBUTES]",attrs)

subs=[]
for n in ast.walk(fn):
    if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=="x":
        try: subs.append(ast.unparse(n))
        except Exception: pass
print("[X_SUBSCRIPTS]",sorted(set(subs)))

calls=[]
for n in ast.walk(fn):
    if isinstance(n,ast.Call):
        try: calls.append(ast.unparse(n))
        except Exception: pass
print("[CALLS]")
for c in calls: print(" ",c)

print("[PASS] CHF-010 OAD-261 exact input contract physically recovered")
print("[PRODUCTION_MUTATION]",False)
print("[EXECUTION_AUTHORITY]",False)
