from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_119_phase7_friction_input_census.py"
TEST=ROOT/"test_usls_119_phase7_friction_input_census.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

FIELDS={
 "fee":("fee","fee_lamports","protocol_fee_raw","lp_fee_raw","priority_fee","priority_fee_lamports"),
 "liquidity":("liquidity","liquidity_usd","pool_base_token_reserves_raw","pool_quote_token_reserves_raw",
              "virtual_sol_reserves_after","virtual_token_reserves_after"),
 "latency":("birth_age_seconds","trigger_age_seconds","observed_unix","block_time","trade_observed_unix"),
 "price":("effective_price","price","price_usd"),
 "amounts":("base_amount","quote_amount","base_quantity","quote_quantity","input_amount","output_amount"),
}

def _walk(x,out):
 if isinstance(x,dict):
  out.append(x)
  for v in x.values():_walk(v,out)
 elif isinstance(x,list):
  for v in x:_walk(v,out)

def _has(d,keys):
 return any(k in d and d.get(k) not in (None,"") for k in keys)

def run(root):
 root=Path(root)
 base=root/"runtime_state/solana_opportunities"
 rows=[];families={}
 for p in base.rglob("*.json"):
  if p.stat().st_size>120_000_000:continue
  try:d=json.loads(p.read_text(encoding="utf-8"))
  except Exception:continue
  objs=[];_walk(d,objs)
  counts={k:0 for k in FIELDS}; fams=set()
  for o in objs:
   if not isinstance(o,dict):continue
   fam=o.get("family") or o.get("venue") or o.get("launcher_family")
   if fam:fams.add(str(fam))
   for name,keys in FIELDS.items():
    if _has(o,keys):counts[name]+=1
  if any(counts.values()):
   rows.append({"path":str(p.relative_to(root)),"counts":counts,"families":sorted(fams)[:20]})
   for f in fams:
    z=families.setdefault(str(f),{k:0 for k in FIELDS})
    for k,v in counts.items():z[k]+=v
 return {"revision":"USLS_119","artifact_count":len(rows),
  "family_signal_counts":families,"artifacts":rows,
  "next_boundary":"STRICT_FRICTION_MODEL_INPUT_NORMALIZATION",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase7_friction_input_census.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_119_phase7_friction_input_census import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  fams=len(d["family_signal_counts"])
  print("[STATE]",json.dumps({"artifact_count":d["artifact_count"],
   "family_count":fams,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["artifact_count"],0,"NO_FRICTION_INPUT_ARTIFACTS_DISCOVERED")
  self.assertGreater(fams,0,"NO_FAMILY_FRICTION_INPUTS_DISCOVERED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-119 Phase 7 friction input census")
  print("[PASS] fee/liquidity/latency/price/amount evidence inventoried")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
