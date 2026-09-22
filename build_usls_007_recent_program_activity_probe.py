from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_007_recent_program_activity_probe.py"
TEST=ROOT/"test_usls_007_recent_program_activity_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time,urllib.request
from pathlib import Path
from .usls_006_verified_mainnet_program_registry import RPC

def _rpc(pid):
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress",
  "params":[pid,{"limit":3,"commitment":"confirmed"}]}).encode()
 req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=12) as r:
   d=json.loads(r.read());return d.get("result") or [],None
 except Exception as e:return [],type(e).__name__+":"+str(e)

def probe(root):
 reg=json.loads((Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/verified_mainnet_program_registry.json").read_text(encoding="utf-8"))
 now=time.time();rows=[]
 for x in reg["programs"]:
  sigs,err=_rpc(x["program_id"])
  bt=max((s.get("blockTime") or 0 for s in sigs),default=0)
  rows.append({"family":x["family"],"program_id":x["program_id"],"query_ok":err is None,
   "recent_signature_count":len(sigs),"latest_block_time":bt or None,
   "latest_age_seconds":(now-bt) if bt else None,"error":err})
 return {"revision":"USLS_007","program_count":len(rows),
  "query_success_count":sum(1 for x in rows if x["query_ok"]),
  "programs_with_recent_signatures":sum(1 for x in rows if x["recent_signature_count"]>0),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=probe(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/recent_program_activity.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_007_recent_program_activity_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in (
   "program_count","query_success_count","programs_with_recent_signatures")},sort_keys=True))
  for r in d["rows"]:print("[ACTIVITY]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["query_success_count"],0)
  self.assertGreater(d["programs_with_recent_signatures"],0)
  print("[PASS] USLS-007 recent mainnet program activity probe")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
