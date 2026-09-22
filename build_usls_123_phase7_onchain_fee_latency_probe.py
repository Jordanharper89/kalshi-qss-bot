from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_123_phase7_onchain_fee_latency_probe.py"
TEST=ROOT/"test_usls_123_phase7_onchain_fee_latency_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

def _rpc(method,params,timeout=20.0):
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 return _rpc(method,params,timeout)

def run(root):
 root=Path(root)
 d=json.loads((root/SRC).read_text(encoding="utf-8"))
 chosen={}
 for x in d.get("rows",[]):
  fam=x.get("family");sig=x.get("trade_signature")
  if fam and sig and fam not in chosen:chosen[fam]=x
 rows=[]
 for i,(fam,x) in enumerate(sorted(chosen.items())):
  sig=x["trade_signature"];tx=None;err=None
  try:
   tx=_rpc("getTransaction",[sig,{"commitment":"confirmed","encoding":"jsonParsed",
      "maxSupportedTransactionVersion":1}],20.0)
  except Exception as e:err=repr(e)
  meta=(tx or {}).get("meta") or {}
  block=(tx or {}).get("blockTime")
  obs=x.get("trade_observed_unix")
  latency=None
  if isinstance(obs,(int,float)) and isinstance(block,(int,float)):
   latency=max(0.0,float(obs)-float(block))
  rows.append({"family":fam,"trade_signature":sig,
   "tx_found":isinstance(tx,dict),"rpc_error":err,
   "network_fee_lamports":meta.get("fee"),
   "block_time":block,"observed_unix":obs,
   "observation_latency_seconds":latency,
   "compute_units_consumed":meta.get("computeUnitsConsumed"),
   "execution_authority":False})
  if i+1<len(chosen):time.sleep(0.8)
 by={x["family"]:x for x in rows}
 return {"revision":"USLS_123","family_probe_count":len(rows),
  "tx_found_count":sum(x["tx_found"] for x in rows),
  "fee_found_count":sum(x["network_fee_lamports"] is not None for x in rows),
  "latency_found_count":sum(x["observation_latency_seconds"] is not None for x in rows),
  "rows":rows,"families":by,
  "fee_semantics":"SOLANA_NETWORK_FEE_LAMPORTS_NOT_QUOTE_DENOMINATED_FEE_FRACTION",
  "next_boundary":"SOURCE_NATIVE_LIQUIDITY_AND_FEE_EVIDENCE_EXTRACTION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_onchain_fee_latency_probe.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_123_phase7_onchain_fee_latency_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in (
   "family_probe_count","tx_found_count","fee_found_count","latency_found_count","next_boundary")},sort_keys=True))
  self.assertEqual(d["family_probe_count"],14,"NOT_ALL_14_FAMILIES_PROBED")
  self.assertGreater(d["tx_found_count"],0,"NO_TRANSACTION_READBACK")
  self.assertGreater(d["fee_found_count"],0,"NO_ONCHAIN_NETWORK_FEE_READBACK")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-123 on-chain fee/latency probe")
  print("[PASS] Solana transaction fee evidence physically read without converting it into fake quote fee fractions")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
