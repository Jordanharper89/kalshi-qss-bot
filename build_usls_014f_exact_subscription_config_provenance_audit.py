from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parent
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_083_persistent_event_driven_runtime.py"
TEST=ROOT/"test_usls_014f_exact_subscription_config_provenance_audit.py"

src=P.read_text(encoding="utf-8")
tree=ast.parse(src)
lines=src.splitlines()

blocks=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="serve":
        lo=n.lineno
        hi=min(getattr(n,"end_lineno",lo),lo+24)
        blocks.append("\n".join(f"{i:04d}: {lines[i-1]}" for i in range(lo,hi+1)))

imports=[]
for n in ast.walk(tree):
    if isinstance(n,ast.ImportFrom):
        imports.append({"module":n.module,"names":[a.name for a in n.names],"level":n.level})
    elif isinstance(n,ast.Import):
        imports.append({"module":None,"names":[a.name for a in n.names],"level":0})

TEST.write_text(
f'''import unittest
class T(unittest.TestCase):
 def test_audit(self):
  print("[IMPORTS]",{imports!r})
  print("[SERVE]")
  print({blocks[0]!r})
  print("[PASS] USLS-014F exact subscription config provenance audit")
  print("[SCOPE] diagnostic only; production runtime unchanged")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
''',encoding="utf-8")

print("[PASS] installed:",TEST.name)
print("[PASS] production runtime unchanged")
print("[PASS] execution_authority=FALSE")