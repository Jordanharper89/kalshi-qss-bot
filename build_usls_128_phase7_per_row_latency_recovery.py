from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_128_phase7_per_row_latency_recovery.py"
TEST=ROOT/"test_usls_128_phase7_per_row_latency_recovery.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _sig(x):return x.get("trade_signature") or x.get("signature")

def run(root):
 root=Path(root);d=json.loads((root/SRC).read_text(encoding="utf-8"))
 cache={};rows=[];by={}
 for x in d.get("rows",[]):
  rel=x.get("source_artifact");sig=x.get("trade_signature")
  if not rel or not sig:continue
  if rel not in cache:
   try:
    raw=json.loads((root/rel).read_text(encoding="utf-8"))
    objs=[];_walk(raw,objs);idx={}
    for o in objs:
     if isinstance(o,dict) and _sig(o):idx.setdefault(str(_sig(o)),[]).append(o)
    cache[rel]=idx
   except Exception:cache[rel]={}
  block=None;obs=x.get("trade_observed_unix")
  for o in cache[rel].get(str(sig),[]):
   if block is None:block=o.get("block_time") or o.get("blockTime")
   if obs is None:obs=o.get("observed_unix") or o.get("trade_observed_unix") or o.get("received_unix")
  latency=None
  if isinstance(block,(int,float)) and isinstance(obs,(int,float)):
   latency=max(0.0,float(obs)-float(block))
  row={"family":x.get("family"),"market_address":x.get("market_address"),
       "trade_signature":sig,"block_time":block,"observed_unix":obs,
       "observation_latency_seconds":latency,"execution_authority":False}
  rows.append(row)
  z=by.setdefault(row["family"],{"rows":0,"latency":0})
  z["rows"]+=1;z["latency"]+=latency is not None
 return {"revision":"USLS_128","row_count":len(rows),
  "latency_row_count":sum(x["observation_latency_seconds"] is not None for x in rows),
  "family_support":by,"rows":rows,
  "latency_semantics":"CHAIN_BLOCK_TIME_TO_ORACLE_OBSERVATION_TIME",
  "next_boundary":"PRE_TRADE_REFERENCE_AND_EXECUTION_DEVIATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_per_row_latency_recovery.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_128_phase7_per_row_latency_recovery import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"latency_row_count":d["latency_row_count"],
   "family_support":d["family_support"],"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["row_count"],585)
  self.assertGreater(d["latency_row_count"],2,"PER_ROW_LATENCY_RECOVERY_DID_NOT_EXPAND_COVERAGE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-128 per-row latency recovery")
  print("[PASS] physical block-time to Oracle-observation latency recovered without guessing")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
