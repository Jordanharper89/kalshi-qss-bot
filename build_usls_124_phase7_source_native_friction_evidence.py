from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_124_phase7_source_native_friction_evidence.py"
TEST=ROOT/"test_usls_124_phase7_source_native_friction_evidence.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

SRC="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"
FEE_KEYS=("fee","fee_lamports","protocol_fee_raw","lp_fee_raw","priority_fee","priority_fee_lamports",
          "dex_fee_delta_lamports","helio_fee_delta_lamports")
LIQ_KEYS=("liquidity","liquidity_usd","pool_base_token_reserves_raw","pool_quote_token_reserves_raw",
          "virtual_sol_reserves_after","virtual_token_reserves_after","reserve_a","reserve_b")
PRE_KEYS=("pre_reserve_a","pre_reserve_b","reserves_before","pool_reserves_before")
POST_KEYS=("post_reserve_a","post_reserve_b","reserves_after","pool_reserves_after")

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _sig(o):
 return o.get("trade_signature") or o.get("signature")

def _evidence(o,keys):
 return {k:o.get(k) for k in keys if k in o and o.get(k) not in (None,"")}

def run(root):
 root=Path(root)
 d=json.loads((root/SRC).read_text(encoding="utf-8"))
 cache={};rows=[];fam={}
 for x in d.get("rows",[]):
  rel=x.get("source_artifact");sig=x.get("trade_signature")
  if not rel or not sig:continue
  if rel not in cache:
   try:
    raw=json.loads((root/rel).read_text(encoding="utf-8"))
    objs=[];_walk(raw,objs)
    idx={}
    for o in objs:
     if isinstance(o,dict):
      s=_sig(o)
      if s:idx.setdefault(str(s),[]).append(o)
    cache[rel]=idx
   except Exception:cache[rel]={}
  matches=cache[rel].get(str(sig),[])
  fees={};liq={};pre={};post={}
  for o in matches:
   fees.update(_evidence(o,FEE_KEYS));liq.update(_evidence(o,LIQ_KEYS))
   pre.update(_evidence(o,PRE_KEYS));post.update(_evidence(o,POST_KEYS))
  row={"family":x.get("family"),"trade_signature":sig,
   "source_artifact":rel,"fee_evidence":fees,"liquidity_evidence":liq,
   "pre_trade_reserve_evidence":pre,"post_trade_reserve_evidence":post,
   "fee_supported":bool(fees),"liquidity_supported":bool(liq),
   "pre_trade_reference_supported":bool(pre),
   "execution_authority":False}
  rows.append(row)
  z=fam.setdefault(row["family"],{"rows":0,"fee":0,"liquidity":0,"pre_reference":0})
  z["rows"]+=1;z["fee"]+=row["fee_supported"];z["liquidity"]+=row["liquidity_supported"]
  z["pre_reference"]+=row["pre_trade_reference_supported"]
 return {"revision":"USLS_124","row_count":len(rows),"family_support":fam,"rows":rows,
  "slippage_policy":"NO_SLIPPAGE_CLAIM_WITHOUT_PRE_TRADE_REFERENCE_STATE",
  "next_boundary":"MERGE_PHYSICAL_FRICTION_EVIDENCE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_source_native_friction_evidence.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_124_phase7_source_native_friction_evidence import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  fee=sum(v["fee"] for v in d["family_support"].values())
  liq=sum(v["liquidity"] for v in d["family_support"].values())
  pre=sum(v["pre_reference"] for v in d["family_support"].values())
  print("[STATE]",json.dumps({"row_count":d["row_count"],"fee_rows":fee,
   "liquidity_rows":liq,"pre_reference_rows":pre,
   "family_support":d["family_support"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(fee+liq,0,"NO_SOURCE_NATIVE_FRICTION_EVIDENCE_FOUND")
  self.assertEqual(d["slippage_policy"],"NO_SLIPPAGE_CLAIM_WITHOUT_PRE_TRADE_REFERENCE_STATE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-124 source-native friction evidence")
  print("[PASS] fee/liquidity/reserve evidence preserved without invented slippage")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
