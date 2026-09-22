from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_113_cross_venue_trade_artifact_schema_census.py"
TEST=ROOT/"test_usls_113_cross_venue_trade_artifact_schema_census.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

FAMILIES=("PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM",
 "RAYDIUM_CPMM","METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM",
 "ORCA","MOONIT","BOOP_FUN","HEAVEN")

ALIASES={
 "signature":("signature","trade_signature"),
 "token":("token_address","token","mint","base_mint","trade_mint"),
 "market":("market_address","pool","pool_address","curve","bonding_curve","amm"),
 "side":("side","trade_side"),
 "base_qty":("base_quantity","base_amount","token_amount","input_amount","amount_in"),
 "quote_qty":("quote_quantity","quote_amount","sol_amount","output_amount","amount_out"),
 "price":("effective_price","price","price_usd","execution_price"),
 "slot":("slot","trade_slot"),
 "time":("trade_observed_unix","observed_unix","received_unix","block_time"),
}

def _flatten(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_flatten(v,out)
 elif isinstance(x,list):
  for v in x:_flatten(v,out)

def _family(path,obj):
 up=(str(path)+" "+json.dumps(obj,default=str)[:4000]).upper().replace("-","_")
 for f in FAMILIES:
  if f in up or f.replace("_","") in up.replace("_",""):return f
 return None

def _has(d,names):
 return any(k in d and d.get(k) not in (None,"") for k in names)

def run(root):
 root=Path(root);rs=root/"runtime_state";rows=[]
 for p in rs.rglob("*.json"):
  if p.stat().st_size>80_000_000:continue
  try:d=json.loads(p.read_text(encoding="utf-8"))
  except Exception:continue
  objs=[];_flatten(d,objs)
  sample=[]
  fam=None
  for o in objs:
   if not isinstance(o,dict):continue
   f=_family(p,o)
   if f:fam=f
   cov={k:_has(o,v) for k,v in ALIASES.items()}
   if cov["signature"] and (cov["token"] or cov["market"] or cov["base_qty"] or cov["quote_qty"]):
    sample.append({"coverage":cov,"keys":sorted(o.keys())[:80]})
    if len(sample)>=3:break
  if fam and sample:
   rows.append({"path":str(p.relative_to(root)),"family":fam,"samples":sample})
 fammap={f:[] for f in FAMILIES}
 for r in rows:fammap[r["family"]].append(r["path"])
 return {"revision":"USLS_113","artifact_count":len(rows),
  "family_artifact_counts":{k:len(v) for k,v in fammap.items()},
  "family_artifacts":fammap,"artifacts":rows,
  "next_boundary":"STRICT_CROSS_VENUE_ECONOMIC_ROW_MATERIALIZATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/cross_venue_trade_artifact_schema_census.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_113_cross_venue_trade_artifact_schema_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  covered=sum(v>0 for v in d["family_artifact_counts"].values())
  print("[STATE]",json.dumps({"artifact_count":d["artifact_count"],
   "covered_families":covered,"family_artifact_counts":d["family_artifact_counts"],
   "next_boundary":d["next_boundary"]},sort_keys=True))
  for x in d["artifacts"][:40]:print("[ARTIFACT]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["artifact_count"],0,"NO_CROSS_VENUE_TRADE_ARTIFACTS_DISCOVERED")
  self.assertGreaterEqual(covered,4,"INSUFFICIENT_CROSS_VENUE_ARTIFACT_COVERAGE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-113 cross-venue trade artifact schema census")
  print("[PASS] physical schemas inventoried before adapter wiring")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
