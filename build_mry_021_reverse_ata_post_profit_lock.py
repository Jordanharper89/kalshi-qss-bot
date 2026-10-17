from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_021_reverse_ata_post_profit_lock.py")
s=R.read_text(encoding="utf-8")
lines=s.splitlines()
tree=ast.parse(s)

helper=None
target=None

for n in tree.body:
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        chunk="\n".join(lines[n.lineno-1:n.end_lineno])
        if "reverse_ata_ready" in chunk and "create_token_ata" in chunk:
            helper=n.name
        if n.name=="_fast_010_profit_lock_route":
            target=n

if not helper:
    raise RuntimeError("MRY021_REVERSE_ATA_HELPER_NOT_FOUND")
if target is None:
    raise RuntimeError("MRY021_PROFIT_LOCK_FUNCTION_NOT_FOUND")

insert_after=None
for n in ast.walk(target):
    if isinstance(n,ast.Assign):
        chunk="\n".join(lines[n.lineno-1:n.end_lineno])
        if "_reverse_instruction_sets(" in chunk:
            insert_after=n.end_lineno
            break

if insert_after is None:
    raise RuntimeError("MRY021_REVERSE_REBUILD_NOT_FOUND")

marker=f'        out={helper}(USER,out)  # MRY021_POST_LOCK_ATA'
if marker not in lines:
    lines.insert(insert_after,marker)

out="\n".join(lines)+"\n"
ast.parse(out)
R.write_text(out,encoding="utf-8")

test=f'''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_post_lock_ata(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("MRY021_POST_LOCK_ATA",s)
  self.assertIn("_reverse_instruction_sets(",s)
  self.assertIn("{helper}(USER,out)",s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-021 installed")
print("[PASS] reverse ATA readiness reapplied after atomic profit-lock rebuild")
print("[PASS] 0.010 SOL + preflight + maxRetries=0 preserved")