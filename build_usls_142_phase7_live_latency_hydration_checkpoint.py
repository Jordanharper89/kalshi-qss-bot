from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_142_phase7_live_latency_hydration_checkpoint.py"
TEST=ROOT/"test_usls_142_phase7_live_latency_hydration_checkpoint.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/phase7_live_missing_venue_latency_cohort.json"

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"))
 chosen={}
 for x in d.get("rows",[]):
  f=x.get("family");sig=x.get("trade_signature")
  if f and sig and f not in chosen:chosen[f]=x
 rows=[]
 for i,(f,x) in enumerate(sorted(chosen.items())):
  tx=None;err=None
  try:
   tx=_rpc("getTransaction",[x["trade_signature"],{"commitment":"confirmed",
      "encoding":"jsonParsed","maxSupportedTransactionVersion":1}],20.0)
  except Exception as e:err=repr(e)
  block=(tx or {}).get("blockTime")
  obs=x.get("observed_unix") or x.get("captured_unix")
  latency=(max(0.0,float(obs)-float(block))
           if isinstance(obs,(int,float)) and isinstance(block,(int,float)) else None)
  rows.append({"family":f,"trade_signature":x["trade_signature"],"tx_found":isinstance(tx,dict),
   "block_time":block,"observed_unix":obs,"observation_latency_seconds":latency,
   "network_fee_lamports":((tx or {}).get("meta") or {}).get("fee"),
   "rpc_error":err,"execution_authority":False})
  if i+1<len(chosen):time.sleep(0.7)
 return {"revision":"USLS_142","family_probe_count":len(rows),
  "tx_found_count":sum(x["tx_found"] for x in rows),
  "latency_ready_count":sum(x["observation_latency_seconds"] is not None for x in rows),
  "families_with_latency":[x["family"] for x in rows if x["observation_latency_seconds"] is not None],
  "rows":rows,"phase7_status":"IN_PROGRESS",
  "next_boundary":"EXACT_LIVE_FRICTION_NORMALIZATION_FOR_OBSERVED_MISSING_VENUES",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_live_latency_hydration_checkpoint.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_142_phase7_live_latency_hydration_checkpoint import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "family_probe_count","tx_found_count","latency_ready_count",
   "families_with_latency","phase7_status","next_boundary")},sort_keys=True))
  self.assertGreater(d["family_probe_count"],0)
  self.assertGreater(d["tx_found_count"],0,"NO_LIVE_MISSING_VENUE_TRANSACTION_READBACK")
  self.assertGreater(d["latency_ready_count"],0,"NO_LIVE_MISSING_VENUE_LATENCY_RECOVERED")
  self.assertEqual(d["phase7_status"],"IN_PROGRESS")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-142 live latency hydration checkpoint")
  print("[PASS] real prospective missing-venue latency physically recovered")
  print("[NEXT] EXACT_LIVE_FRICTION_NORMALIZATION_FOR_OBSERVED_MISSING_VENUES")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
