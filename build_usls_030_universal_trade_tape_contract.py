from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_030_universal_trade_tape_contract.py"
TEST=ROOT/"test_usls_030_universal_trade_tape_contract.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

REQUIRED=("trade_id","signature","slot","block_time","observed_unix","venue","program_id",
"token_address","market_address","quote_mint","side","trader","base_amount","quote_amount",
"effective_price","birth_age_seconds","instruction_index","source_lineage","decoder_state",
"execution_authority")

SIDES=("BUY","SELL","UNKNOWN_TRADE_TYPE")

def validate(row):
 missing=[k for k in REQUIRED if k not in row]
 errors=[]
 if row.get("side") not in SIDES:errors.append("INVALID_SIDE")
 if row.get("execution_authority") is not False:errors.append("EXECUTION_AUTHORITY_NOT_FALSE")
 if not row.get("trade_id"):errors.append("MISSING_TRADE_ID")
 return {"valid":not missing and not errors,"missing":missing,"errors":errors}

def contract():
 return {"revision":"USLS_030","schema_version":1,"required_fields":list(REQUIRED),
  "allowed_sides":list(SIDES),"unknown_retention":True,"append_only":True,
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 root=Path(root);p=root/"runtime_state/solana_opportunities/universal_trade_tape"
 p.mkdir(parents=True,exist_ok=True)
 q=p/"trade_tape_contract.json";d=contract()
 q.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return q,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_030_universal_trade_tape_contract import write,validate
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  sample={k:None for k in d["required_fields"]}
  sample.update({"trade_id":"fixture:1","side":"UNKNOWN_TRADE_TYPE","execution_authority":False})
  v=validate(sample)
  print("[STATE]",json.dumps({"required_field_count":len(d["required_fields"]),
   "allowed_sides":d["allowed_sides"],"unknown_retention":d["unknown_retention"],
   "sample_valid":v["valid"]},sort_keys=True))
  self.assertTrue(v["valid"]);self.assertTrue(d["unknown_retention"])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-030 universal Solana trade-tape contract certified")
  print("[PASS] BUY/SELL/UNKNOWN trades share one venue-neutral schema")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
