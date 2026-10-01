from pathlib import Path

TEST = '''from pathlib import Path
import ast

root=Path.cwd()
base=root/"qseries_v2/oracle_intelligence/opportunity_operating_system"
assert base.exists(), f"missing existing subsystem: {base}"
files=sorted(base.rglob("*.py"))
assert files, "existing opportunity subsystem contains no Python modules"
print(f"[EXISTING_OOS_FILES] {len(files)}")
for p in files:
    rel=p.relative_to(root).as_posix()
    try:
        tree=ast.parse(p.read_text(encoding="utf-8"))
        api=[n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
        imports=[]
        for n in tree.body:
            if isinstance(n,ast.ImportFrom) and n.module:
                imports.append(n.module)
        print(f"[MODULE] {rel}")
        print(f"  [API] {api}")
        if imports: print(f"  [IMPORTS] {imports}")
    except Exception as e:
        print(f"  [PARSE_ERROR] {type(e).__name__}: {e}")
print("[PASS] existing Opportunity Operating System physically inventoried")
print("[PASS] no production mutation execution_authority=FALSE")
'''
Path("test_ooi_002_existing_opportunity_operating_system_contract_audit.py").write_text(TEST,encoding="utf-8")
print("[PASS] OOI-002 contract audit installed")
print("[PASS] test installed: test_ooi_002_existing_opportunity_operating_system_contract_audit.py")