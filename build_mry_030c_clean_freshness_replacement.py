from pathlib import Path
import ast

R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
T=Path("test_mry_030c_clean_freshness_replacement.py")
s=R.read_text(encoding="utf-8")

a=s.find("def _fast_010_refresh_latest")
b=s.find("def fast_live_attack",a)

if a<0:
    raise RuntimeError("MRY030C_REFRESH_START_NOT_FOUND")
if b<0:
    raise RuntimeError("MRY030C_FAST_ATTACK_BOUNDARY_NOT_FOUND")

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

candidate=s[:a]+new+s[b:]

try:
    ast.parse(candidate)
except SyntaxError as e:
    print("[FAIL] runtime still has syntax error outside replaced MRY-030 function")
    print("[SYNTAX] line=%s offset=%s msg=%s"%(e.lineno,e.offset,e.msg))
    if e.lineno:
        rows=candidate.splitlines()
        for i in range(max(0,e.lineno-3),min(len(rows),e.lineno+2)):
            print("[LINE %d] %r"%(i+1,rows[i]))
    raise

R.write_text(candidate,encoding="utf-8")

test='''import ast,unittest
from pathlib import Path
R=Path("qseries_v2/oracle_execution/solana_atomic_executor/runtime.py")
class T(unittest.TestCase):
 def test_runtime(self):
  s=R.read_text(); ast.parse(s)
  a=s.index("def _fast_010_refresh_latest")
  b=s.index("def fast_live_attack",a)
  f=s[a:b]
  self.assertEqual(f.count("lane.latest.get(token)"),1)
  self.assertEqual(f.count("exact_snapshot_opportunities"),1)
  self.assertNotIn("while refreshes<",f)
  self.assertIn("FAST_010_SINGLE_REFRESH",f)
 def test_guards(self):
  s=R.read_text()
  self.assertIn('"skipPreflight":False',s)
  self.assertIn('"maxRetries":0',s)
  self.assertIn("CANARY_TRADE_LAMPORTS=10_000_000",s)
if __name__=="__main__": unittest.main(verbosity=2)
'''
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-030C clean freshness replacement installed")
print("[PASS] complete runtime AST parses")
print("[PASS] one RAM lookup + at most one reprice")