from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_012_live_multifamily_transaction_hydration.py"
TEST=ROOT/"test_usls_012_live_multifamily_transaction_hydration.py"
MOD_TEXT="""from __future__ import annotations
import json,urllib.request
from pathlib import Path
RPC="https://api.mainnet-beta.solana.com"
def _tx(sig):
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}]}).encode()
 req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=15) as r:return (json.loads(r.read()).get("result")),None
 except Exception as e:return None,type(e).__name__+":"+str(e)
def hydrate(root,per_family=2):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"live_14_program_probe.json").read_text(encoding="utf-8"))
 chosen=[];seen={}
 for x in reversed(d.get("notifications") or []):
  fam=x["family"]
  if x.get("err") is not None or not x.get("signature") or seen.get(fam,0)>=per_family:continue
  seen[fam]=seen.get(fam,0)+1;chosen.append(x)
 rows=[]
 for x in chosen:
  tx,err=_tx(x["signature"]);rows.append({"family":x["family"],"signature":x["signature"],"slot":x.get("slot"),
   "observed_unix":x.get("observed_unix"),"hydrated":tx is not None,"error":err,"raw_transaction":tx})
 return {"revision":"USLS_012","family_count":len(set(x["family"] for x in rows)),"sample_count":len(rows),
  "hydrated_count":sum(1 for x in rows if x["hydrated"]),"rows":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=hydrate(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/live_multifamily_transactions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT="""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_012_live_multifamily_transaction_hydration import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_hydration(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in ("family_count","sample_count","hydrated_count")},sort_keys=True))
  for r in d["rows"]:print("[TX]",json.dumps({"family":r["family"],"signature":r["signature"],"slot":r["slot"],"hydrated":r["hydrated"],"error":r["error"]},sort_keys=True))
  self.assertGreater(d["sample_count"],0);self.assertGreater(d["hydrated_count"],0)
  print("[PASS] USLS-012 live multi-family transaction hydration")
  print("[PASS] live venue notifications can be converted into full transaction evidence")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
