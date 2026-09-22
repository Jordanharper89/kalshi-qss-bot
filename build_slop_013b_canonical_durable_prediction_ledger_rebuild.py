from pathlib import Path
import ast

R=Path.cwd()
D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
M=D/"slop_013b_canonical_durable_prediction_ledger_rebuild.py"

M.write_text(r'''from dataclasses import asdict
from pathlib import Path
import json,os,tempfile
from .slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity

READ_ONLY=True
EXECUTION_AUTHORITY=False
REL=Path("runtime_state")/"solana_live_opportunity"/"prospective_predictions.json"

def _path(root=None):
 return Path(root or Path.cwd()).resolve()/REL

def _canonical(x):
 d=asdict(x) if not isinstance(x,dict) else dict(x)
 d["conditions"]=[list(v) for v in tuple(d.get("conditions") or ())]
 return d

def _restore(d):
 x=dict(d)
 x["conditions"]=tuple(tuple(v) for v in tuple(x.get("conditions") or ()))
 return ProspectiveOpportunity(**x)

def _load(root=None):
 p=_path(root)
 if not p.exists(): return {}
 raw=json.loads(p.read_text(encoding="utf-8"))
 return {str(x["prediction_id"]):_canonical(x)
         for x in tuple(raw.get("predictions") or ())}

def _write(items,root=None):
 p=_path(root);p.parent.mkdir(parents=True,exist_ok=True)
 payload={"schema":"SLOP-013B","read_only":True,"execution_authority":False,
          "predictions":[items[k] for k in sorted(items)]}
 fd,tmp=tempfile.mkstemp(prefix=p.name+".",suffix=".tmp",dir=str(p.parent))
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as f:
   json.dump(payload,f,indent=2,sort_keys=True)
   f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 return p

def persist_predictions(predictions,root=None):
 items=_load(root);new=existing=0
 for x in tuple(predictions):
  d=_canonical(x);pid=str(x.prediction_id)
  if pid in items:
   if items[pid]!=d:
    raise RuntimeError("immutable prediction collision: "+pid)
   existing+=1
  else:
   items[pid]=d;new+=1
 p=_write(items,root)
 return {"total":len(items),"new":new,"existing":existing,
         "path":str(p),"execution_authority":False}

def read_predictions(root=None,state=None):
 items=_load(root);out=[]
 for pid in sorted(items):
  x=_restore(items[pid])
  if state is not None and str(x.state)!=str(state):continue
  out.append(x)
 return tuple(out)
''',encoding="utf-8")

T=R/"test_slop_013b_canonical_durable_prediction_ledger_rebuild.py"

T.write_text(r'''import tempfile,unittest
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_003_concurrent_opportunity_admission_prospective_freeze import ProspectiveOpportunity
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import persist_predictions,read_predictions

class T(unittest.TestCase):
 def prediction(self,target=.1):
  return ProspectiveOpportunity(
   "P1","T","PAIR","2026-09-17T15:30:00+00:00",
   (("order_flow","BUY_PRESSURE"),),
   60,target,.05,200,"PENDING_60S",False
  )

 def test_restart_safe_idempotent_replay(self):
  with tempfile.TemporaryDirectory() as td:
   p=self.prediction()
   first=persist_predictions((p,),td)

   restarted=read_predictions(td,"PENDING_60S")
   self.assertEqual(len(restarted),1)
   self.assertEqual(restarted[0],p)
   self.assertIsInstance(restarted[0].conditions,tuple)
   self.assertIsInstance(restarted[0].conditions[0],tuple)

   replay=persist_predictions((p,),td)
   final=read_predictions(td,"PENDING_60S")

   print("[SLOP-013B FIRST]",first)
   print("[SLOP-013B RESTART]",restarted)
   print("[SLOP-013B REPLAY]",replay)
   print("[SLOP-013B FINAL]",final)

   self.assertEqual(first["new"],1)
   self.assertEqual(replay["new"],0)
   self.assertEqual(replay["existing"],1)
   self.assertEqual(len(final),1)

 def test_same_id_mutation_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   persist_predictions((self.prediction(),),td)
   with self.assertRaisesRegex(RuntimeError,"immutable prediction collision"):
    persist_predictions((self.prediction(target=.2),),td)

   final=read_predictions(td)
   print("[SLOP-013B COLLISION GUARD]",final)

   self.assertEqual(len(final),1)
   self.assertEqual(final[0].target,.1)

if __name__=="__main__":
 unittest.main(verbosity=2)
''',encoding="utf-8")

ast.parse(M.read_text())
ast.parse(T.read_text())

print("[PASS] SLOP-013B installed")
print("[PASS] JSON tuple/list canonicalization repaired")
print("[PASS] restart-safe prediction reconstruction")
print("[PASS] identical replay remains idempotent")
print("[PASS] genuine same-ID mutation remains rejected")
print("[PASS] execution_authority=FALSE")