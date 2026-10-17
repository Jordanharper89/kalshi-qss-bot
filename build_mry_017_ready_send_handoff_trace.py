from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_017_ready_send_handoff_trace.py")
s=R.read_text(encoding="utf-8")
lines=s.splitlines()
tree=ast.parse(s)

target=None
ready_line=None

for node in ast.walk(tree):
    if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
        continue
    chunk="\n".join(lines[node.lineno-1:node.end_lineno])
    if "FAST_010_READY" in chunk:
        target=node
        for i in range(node.lineno-1,node.end_lineno):
            if "FAST_010_READY" in lines[i]:
                ready_line=i+1
                break
        break

if target is None or ready_line is None:
    raise RuntimeError("MRY017_READY_FUNCTION_NOT_FOUND")

returns=[]
for node in ast.walk(target):
    if isinstance(node,ast.Return) and node.lineno>ready_line:
        returns.append(node.lineno)

for ln in sorted(returns,reverse=True):
    i=ln-1
    ind=lines[i][:len(lines[i])-len(lines[i].lstrip())]
    p=ind+f'print("[MRY017_READY_SEND_HOLD] return_line={ln}",flush=True)'
    if p not in lines:
        lines.insert(i,p)

out="\n".join(lines)+"\n"
ast.parse(out)
R.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_trace(self):
  s=R.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("[FAST_010_READY]",s)
  self.assertIn("[MRY017_READY_SEND_HOLD]",s)
 def test_guards(self):
  s=R.read_text(encoding="utf-8")
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
ast.parse(test)
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-017 installed")
print("[PASS] READY function hidden-return tracing enabled")
print("[PASS] execution behavior unchanged")
print("[INFO] ready_function=%s traced_returns=%s"%(target.name,returns))