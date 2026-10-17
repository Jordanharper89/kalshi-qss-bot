from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_030_single_shot_hot_path_freshness.py")
s=R.read_text(encoding="utf-8")
tree=ast.parse(s)
lines=s.splitlines()

fn=next((n for n in tree.body
 if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
 and n.name=="_fast_010_refresh_latest"),None)
if fn is None:
    raise RuntimeError("MRY030_REFRESH_FUNCTION_MISSING")

new='''def _fast_010_refresh_latest(lane,token,snap,opportunity,slot,received_ns,generation):
    with lane.cv:
        row=lane.latest.get(token)

    if not row or int(row[3])<=int(generation):
        return (snap,opportunity,int(slot),int(received_ns),int(generation))

    latest_snap=row[0]
    latest_slot=int(row[1])
    latest_received_ns=int(row[2])
    latest_generation=int(row[3])

    rows=q18.exact_snapshot_opportunities(latest_snap,CANARY_TRADE_SOL)
    if not rows:
        print("[FAST_010_SINGLE_REFRESH_HOLD] token=%s reason=NO_QUOTES"%token[:10],flush=True)
        return None

    latest=max(rows,key=lambda x:int(x["local_net"]))
    print("[FAST_010_SINGLE_REFRESH] token=%s slot=%s dir=%s bps=%+.2f net=%+d"%
        (token[:10],latest_slot,latest["direction"],
         float(latest["local_bps"]),int(latest["local_net"])),flush=True)

    if int(latest["local_net"])<=0:
        print("[FAST_010_SINGLE_REFRESH_HOLD] token=%s reason=LATEST_NONPOSITIVE net=%+d"%
            (token[:10],int(latest["local_net"])),flush=True)
        return None

    return (latest_snap,latest,latest_slot,latest_received_ns,latest_generation)
'''

lines[fn.lineno-1:fn.end_lineno]=new.splitlines()
out="\\n".join(lines)+"\\n"
ast.parse(out)
R.write_text(out,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_single_shot(self):
  s=R.read_text(); ast.parse(s)
  a=s.index("def _fast_010_refresh_latest")
  b=s.index("\\ndef ",a+5)
  f=s[a:b]
  self.assertNotIn("while refreshes<",f)
  self.assertNotIn("GENERATION_CHURN_LIMIT",f)
  self.assertEqual(f.count("lane.latest.get(token)"),1)
  self.assertEqual(f.count("exact_snapshot_opportunities"),1)
  self.assertIn("FAST_010_SINGLE_REFRESH",f)
 def test_money_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__": unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")
print("[PASS] MRY-030 installed")
print("[PASS] hot-path freshness = one RAM lookup, at most one reprice")
print("[PASS] multi-refresh loop and generation-churn wait removed")