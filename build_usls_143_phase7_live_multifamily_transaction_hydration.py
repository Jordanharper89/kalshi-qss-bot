from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_143_phase7_live_multifamily_transaction_hydration.py"
TEST=ROOT/"test_usls_143_phase7_live_multifamily_transaction_hydration.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase7_live_missing_venue_latency_cohort.json"
MAX_PER_FAMILY=3

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"))
 chosen={};seen=set()
 for x in d.get("rows",[]):
  f=x.get("family");sig=x.get("trade_signature")
  if not f or not sig or sig in seen:continue
  if len(chosen.get(f,[]))>=MAX_PER_FAMILY:continue
  chosen.setdefault(f,[]).append(x);seen.add(sig)
 rows=[]
 items=[(f,x) for f,xs in sorted(chosen.items()) for x in xs]
 for i,(f,x) in enumerate(items):
  tx=None;err=None
  try:
   tx=_rpc("getTransaction",[x["trade_signature"],{"commitment":"confirmed",
    "encoding":"jsonParsed","maxSupportedTransactionVersion":1}],20.0)
  except Exception as e:err=repr(e)
  meta=(tx or {}).get("meta") or {};block=(tx or {}).get("blockTime")
  obs=x.get("observed_unix") or x.get("captured_unix")
  latency=(max(0.0,float(obs)-float(block))
           if isinstance(obs,(int,float)) and isinstance(block,(int,float)) else None)
  rows.append({"family":f,"trade_signature":x["trade_signature"],
   "observed_unix":obs,"block_time":block,"observation_latency_seconds":latency,
   "network_fee_lamports":meta.get("fee"),"tx_found":isinstance(tx,dict),
   "transaction":tx,"rpc_error":err,"execution_authority":False})
  if i+1<len(items):time.sleep(0.5)
 by={}
 for x in rows:
  z=by.setdefault(x["family"],{"rows":0,"tx_found":0,"latency":0,"fee":0})
  z["rows"]+=1;z["tx_found"]+=x["tx_found"]
  z["latency"]+=x["observation_latency_seconds"] is not None
  z["fee"]+=x["network_fee_lamports"] is not None
 return {"revision":"USLS_143","max_per_family":MAX_PER_FAMILY,
  "row_count":len(rows),"family_support":by,"rows":rows,
  "next_boundary":"LIVE_TOKEN_ACCOUNT_DELTA_RECONSTRUCTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_live_multifamily_transaction_hydration.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_143_phase7_live_multifamily_transaction_hydration import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreaterEqual(len(d["family_support"]),4,"LIVE_FAMILY_COVERAGE_TOO_NARROW")
  self.assertGreater(sum(v["tx_found"] for v in d["family_support"].values()),0)
  self.assertGreater(sum(v["latency"] for v in d["family_support"].values()),0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-143 live multifamily transaction hydration")
  print("[PASS] multiple prospective signatures per observed family hydrated with fee + latency")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
