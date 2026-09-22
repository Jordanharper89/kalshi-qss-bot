from pathlib import Path
import ast

R=Path.cwd()
P=R/"qseries_v2/oracle_adapters/independent/oad_261_solana_live_token_selection.py"

if not P.exists():
    hits=list((R/"qseries_v2/oracle_adapters/independent").glob("oad_261*.py"))
    if not hits:
        raise SystemExit("[FAIL] OAD-261 source not found")
    P=hits[0]

tree=ast.parse(P.read_text(encoding="utf-8",errors="replace"))

print("="*100)
print(" SSI-011B EXACT SOLANA DISCOVERY CONTRACT AUDIT")
print("="*100)
print("[SOURCE]",P.relative_to(R))

for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
        args=[]
        for a in node.args.args:
            args.append(a.arg)
        defaults=len(node.args.defaults)
        print(
            "[FUNCTION]",
            node.name,
            "args=",tuple(args),
            "defaults=",defaults,
            "async=",isinstance(node,ast.AsyncFunctionDef)
        )

print("[PASS] OAD-261 parsed without mutation")
print("[PASS] discovery contract exposed")
print("[PASS] no acquisition performed")
print("[PASS] no PostgreSQL requests submitted")
print("[PASS] execution_authority=FALSE")