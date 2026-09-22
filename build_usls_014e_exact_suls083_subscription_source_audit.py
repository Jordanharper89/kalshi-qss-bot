from pathlib import Path
import ast,re

ROOT=Path(__file__).resolve().parent
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_083_persistent_event_driven_runtime.py"
TEST=ROOT/"test_usls_014e_exact_suls083_subscription_source_audit.py"

if not P.exists():
    raise SystemExit("SULS_083_NOT_FOUND")

src=P.read_text(encoding="utf-8")
tree=ast.parse(src)
lines=src.splitlines()

hits=[]
terms=("logssubscribe","websockets.connect","ws.send","subscribe","dbc","damm","mentions","program")
for i,line in enumerate(lines,1):
    if any(t in line.lower() for t in terms):
        lo=max(1,i-3);hi=min(len(lines),i+5)
        hits.append((i,lo,hi,"\n".join(f"{n:04d}: {lines[n-1]}" for n in range(lo,hi+1))))

funcs=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
        body=ast.get_source_segment(src,n) or ""
        if any(t in body.lower() for t in ("logssubscribe","ws.send","websocket")):
            funcs.append({"name":n.name,"line":n.lineno,"end":getattr(n,"end_lineno",None)})

test=f'''from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  print("[STATE]",json.dumps({{"hit_count":{len(hits)},"functions":{funcs!r}}},sort_keys=True))
'''
for i,lo,hi,block in hits[:25]:
    safe=repr(block)
    test+=f'  print("[HIT] line={i} range={lo}-{hi}")\n  print({safe})\n'
test+='''  print("[PASS] USLS-014E exact SULS-083 subscription source audit")
  print("[SCOPE] diagnostic only; production runtime unchanged")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
'''

TEST.write_text(test,encoding="utf-8")
print("[PASS] installed audit:",TEST.name)
print("[PASS] production runtime unchanged")
print("[PASS] execution_authority=FALSE")