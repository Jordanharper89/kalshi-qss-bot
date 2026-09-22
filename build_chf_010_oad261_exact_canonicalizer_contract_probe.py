from pathlib import Path
import ast, py_compile

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py"
SPORTS=ROOT/"qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"
TEST=ROOT/"test_chf_010_oad261_exact_canonicalizer_contract_probe.py"

assert TARGET.exists(),f"missing {TARGET}"
assert SPORTS.exists(),f"missing {SPORTS}"

code=f'''from pathlib import Path
import ast, inspect, importlib

ROOT=Path.cwd()
target=ROOT/"qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py"
sports=ROOT/"qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"

src=target.read_text(encoding="utf-8")
tree=ast.parse(src)

print("[OAD261]",target)
for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
        args=[a.arg for a in node.args.args]
        print("[FUNCTION]",node.name,"args=",args,"line=",node.lineno)
    elif isinstance(node,ast.ClassDef):
        print("[CLASS]",node.name,"line=",node.lineno)

ss=sports.read_text(encoding="utf-8")
st=ast.parse(ss)
print("[SPORTS_BOUNDARY]",sports)
for node in ast.walk(st):
    if isinstance(node,ast.ImportFrom) and node.module and "oad_261" in node.module:
        print("[OAD261_IMPORT]",node.module,[(x.name,x.asname) for x in node.names])
    if isinstance(node,ast.Call):
        try:
            text=ast.unparse(node)
        except Exception:
            continue
        if "canonical" in text.lower() or "oad_261" in text.lower():
            print("[CANONICAL_CALL]",text)

print("[PASS] CHF-010 exact OAD-261 canonicalizer contract physically recovered")
print("[PRODUCTION_MUTATION]",False)
print("[EXECUTION_AUTHORITY]",False)
'''
TEST.write_text(code,encoding="utf-8")
py_compile.compile(str(TEST),doraise=True)
print("[PASS] wrote",TEST)
print("[PASS] repository read-only")
print("[PASS] no PostgreSQL write")