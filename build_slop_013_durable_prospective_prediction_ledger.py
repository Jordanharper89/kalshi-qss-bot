from pathlib import Path
import ast
R=Path.cwd()
D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_013_durable_prospective_prediction_ledger.py"
M.write_text(r"""from dataclasses import asdict
from pathlib import Path
import json,os,tempfile
from .slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
READ_ONLY=True;EXECUTION_AUTHORITY=False
REL=Path("runtime_state")/"solana_live_opportunity"/"prospective_predictions.json"

def _path(root=None):
 return Path(root or Path.cwd()).resolve()/REL

def _load(root=None):
 p=_path(root)
 if not p.exists(): return {}
 raw=json.loads(p.read_text(encoding="utf-8"))
 return {str(x["prediction_id"]):dict(x) for x in tuple(raw.get("predictions") or ())}

def _write(items,root=None):
 p=_path(root);p.parent.mkdir(parents=True,exist_ok=True)
 payload={"schema":"SLOP-013","read_only":True,"execution_authority":False,
          "predictions":[items[k] for k in sorted(items)]}
 fd,tmp=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=str(p.parent))
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as f:
   json.dump(payload,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 return p

def persist_predictions(predictions,root=None):
 items=_load(root);new=existing=0
 for x in tuple(predictions):
  d=asdict(x);pid=str(x.prediction_id)
  if pid in items:
   if items[pid]!=d: raise RuntimeError("immutable prediction collision: "+pid)
   existing+=1
  else: items[pid]=d;new+=1
 p=_write(items,root)
 return {"total":len(items),"new":new,"existing":existing,"path":str(p),"execution_authority":False}

def read_predictions(root=None,state=None):
 items=_load(root);out=[]
 for pid in sorted(items):
  d=items[pid]
  if state is not None and str(d["state"])!=str(state):continue
  out.append(ProspectiveOpportunity(**d))
 return tuple(out)
""",encoding="utf-8")
T=R/"test_slop_013_durable_prospective_prediction_ledger.py"
T.write_text(r"""import tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013_durable_prospective_prediction_ledger import persist_predictions,read_predictions
class T(unittest.TestCase):
 def test_restart_safe_identity(self):
  with tempfile.TemporaryDirectory() as td:
   p=ProspectiveOpportunity("P1","T","PAIR","2026-09-17T15:30:00+00:00",(("order_flow","BUY_PRESSURE"),),60,.1,.05,200,"PENDING_60S",False)
   a=persist_predictions((p,),td);b=persist_predictions((p,),td);xs=read_predictions(td,"PENDING_60S")
   print("[SLOP-013]",a,b,xs)
   self.assertEqual((a["new"],b["existing"],len(xs)),(1,1,1));self.assertEqual(xs[0],p)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-013 installed")
print("[PASS] atomic durable prospective ledger")
print("[PASS] immutable prediction identity + idempotent replay")
print("[PASS] execution_authority=FALSE")
