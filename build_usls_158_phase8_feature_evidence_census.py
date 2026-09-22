from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_158_phase8_feature_evidence_census.py"
TEST=ROOT/"test_usls_158_phase8_feature_evidence_census.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

ECON="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"

FIELD_GROUPS={
 "side":("side","trade_side","direction"),
 "trader":("trader","user","wallet","payer","owner"),
 "fee":("fee","fee_lamports","protocol_fee_raw","lp_fee_raw","priority_fee","priority_fee_lamports"),
 "liquidity":("liquidity","liquidity_usd","pool_base_token_reserves_raw","pool_quote_token_reserves_raw",
              "virtual_sol_reserves_after","virtual_token_reserves_after","reserve_a","reserve_b"),
 "time":("trade_observed_unix","observed_unix","block_time","blockTime"),
 "amounts":("base_quantity","quote_quantity","input_amount","output_amount","base_amount","quote_amount"),
}

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _sig(o): return o.get("trade_signature") or o.get("signature")

def run(root):
 root=Path(root)
 econ=json.loads((root/ECON).read_text(encoding="utf-8"))
 cache={};family={}
 for x in econ.get("rows",[]):
  fam=x.get("family");sig=x.get("trade_signature");rel=x.get("source_artifact")
  if not fam or not sig or not rel:continue
  if rel not in cache:
   try:
    raw=json.loads((root/rel).read_text(encoding="utf-8"))
    objs=[];_walk(raw,objs);idx={}
    for o in objs:
     if isinstance(o,dict) and _sig(o):idx.setdefault(str(_sig(o)),[]).append(o)
    cache[rel]=idx
   except Exception:cache[rel]={}
  z=family.setdefault(fam,{"rows":0,**{k:0 for k in FIELD_GROUPS}})
  z["rows"]+=1
  matches=cache[rel].get(str(sig),[])
  merged={}
  for o in matches: merged.update(o)
  merged.update({k:v for k,v in x.items() if v is not None})
  for g,keys in FIELD_GROUPS.items():
   z[g]+=any(merged.get(k) not in (None,"") for k in keys)
 return {"revision":"USLS_158","family_feature_support":family,
  "family_count":len(family),
  "feature_groups":list(FIELD_GROUPS),
  "next_boundary":"ENRICHED_LEAKAGE_SAFE_FEATURE_SNAPSHOTS",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_feature_evidence_census.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_158_phase8_feature_evidence_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"family_count":d["family_count"],
   "family_feature_support":d["family_feature_support"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertEqual(d["family_count"],14)
  self.assertGreater(sum(v["amounts"] for v in d["family_feature_support"].values()),0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-158 Phase 8 feature-evidence census")
  print("[PASS] side/trader/fee/liquidity/time/amount evidence measured across 14 families")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
