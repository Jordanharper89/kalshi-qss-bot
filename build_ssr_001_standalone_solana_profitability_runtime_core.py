from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_profitability_runtime"
MOD=SUB/"ssr_001_runtime_core.py"
TEST=ROOT/"test_ssr_001_standalone_solana_profitability_runtime_core.py"
MOD_TEXT=r"""from __future__ import annotations
import json,os,time,uuid
from pathlib import Path
STATE_REL="runtime_state/solana_opportunities/profitability_runtime/runtime_state.json"
class RuntimeState:
 def __init__(self,root):
  self.root=Path(root);self.path=self.root/STATE_REL;self.path.parent.mkdir(parents=True,exist_ok=True)
  self.boot_id=str(uuid.uuid4());self.started_unix=time.time()
 def read(self):
  if not self.path.exists():return {}
  try:return json.loads(self.path.read_text(encoding="utf-8"))
  except Exception:return {}
 def write(self,**kw):
  cur=self.read();cur.update(kw);cur.update({"boot_id":self.boot_id,"pid":os.getpid(),"heartbeat_unix":time.time(),"execution_authority":False,"read_only":True})
  tmp=self.path.with_suffix(".tmp");tmp.write_text(json.dumps(cur,indent=2,sort_keys=True,default=str),encoding="utf-8");tmp.replace(self.path);return cur
 def boot(self):
  return self.write(service="SOLANA_PROFITABILITY_SCANNER",status="STARTING",started_unix=self.started_unix,cycle_count=0,last_error=None,
   mission="FIND_AND_MEASURE_PROSPECTIVE_NET_TRADEABLE_SOLANA_EDGE_WITHOUT_EXECUTION")
 def running(self,**extra):return self.write(status="RUNNING",**extra)
 def error(self,e):return self.write(status="DEGRADED",last_error=repr(e))
 def stopping(self):return self.write(status="STOPPING")
def contract():
 return {"revision":"SSR_001","service":"SOLANA_PROFITABILITY_SCANNER","standalone_process":True,"separate_from_oracle_runtime":True,
  "execution_authority":False,"read_only":True,"state_path":STATE_REL,"atomic_state_write":True,
  "mission":"PROSPECTIVE_NET_EDGE_DISCOVERY_NOT_INFRASTRUCTURE_FOR_ITS_OWN_SAKE"}
"""
TEST_TEXT=r"""import json,tempfile,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_001_runtime_core import RuntimeState,contract
class T(unittest.TestCase):
 def test_core(self):
  with tempfile.TemporaryDirectory() as td:
   s=RuntimeState(td);a=s.boot();b=s.running(cycle_count=1,prospective_cases=11)
   self.assertEqual(a["status"],"STARTING");self.assertEqual(b["status"],"RUNNING");self.assertEqual(b["cycle_count"],1);self.assertFalse(b["execution_authority"])
   self.assertTrue((Path(td)/contract()["state_path"]).exists())
  print("[STATE]",json.dumps(contract(),sort_keys=True));print("[PASS] SSR-001 standalone Solana profitability runtime core")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);(SUB/"__init__.py").touch();MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")