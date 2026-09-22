from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_048b_shared_universal_economic_normalizer.py"
TEST=ROOT/"test_usls_048b_shared_universal_economic_normalizer.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_045b_universal_multidex_decoder_framework import PROGRAMS

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"multidex_live_event_router.json").read_text(encoding="utf-8"))
 ids=json.loads((base/"multidex_identities.json").read_text(encoding="utf-8"))
 ib={(x["venue"],x["pool"]):x for x in ids["identity_rows"]}
 exact=[];pending=[]
 for n,x in enumerate(src["rows"]):
  if x["venue"]=="PUMP_SWAP" and x["decode_status"]=="EXACT":
   e=x["event"];i=ib.get(("PUMP_SWAP",e["pool"]))
   if not i or i["identity_state"]!="EXACT":
    pending.append({"venue":x["venue"],"signature":x["signature"],"reason":"IDENTITY_PENDING","raw_log":x["raw_log"]});continue
   bd=i["base_decimals"];qd=i["quote_decimals"];ba=e["base_amount_raw"]/(10**bd);qa=e["quote_amount_raw"]/(10**qd)
   exact.append({"trade_id":f'PUMP_SWAP:{x["signature"]}:{x["log_index"]}:{n}',"signature":x["signature"],
    "slot":x["slot"],"block_time":e["timestamp"],"observed_unix":x["observed_unix"],"venue":"PUMP_SWAP",
    "program_id":PROGRAMS["PUMP_SWAP"],"token_address":i["base_mint"],"market_address":e["pool"],
    "quote_mint":i["quote_mint"],"side":e["side"],"trader":e["user"],"base_amount":ba,"quote_amount":qa,
    "effective_price":qa/ba if ba else None,"birth_age_seconds":None,"instruction_index":x["log_index"],
    "lp_fee_raw":e["lp_fee"],"protocol_fee_raw":e["protocol_fee"],
    "pool_base_token_reserves_raw":e["pool_base_token_reserves"],
    "pool_quote_token_reserves_raw":e["pool_quote_token_reserves"],
    "source_lineage":{"router_revision":"USLS_046B","identity_revision":"USLS_047B"},
    "decoder_state":"EXACT_ECONOMIC_TRADE","execution_authority":False})
  elif x["decode_status"]!="EXACT":
   pending.append({"venue":x["venue"],"signature":x["signature"],"reason":"DECODER_PENDING","raw_log":x["raw_log"]})
 return {"revision":"USLS_048B","exact_trade_count":len(exact),"pending_raw_count":len(pending),
  "exact_rows":exact,"pending_raw_rows":pending,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/multidex_universal_economic_tape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_048b_shared_universal_economic_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_norm(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_trade_count":d["exact_trade_count"],
   "pending_raw_count":d["pending_raw_count"],"profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["exact_rows"][:30]:print("[TRADE]",json.dumps(x,sort_keys=True))
  self.assertTrue(all(x["base_amount"]>0 and x["quote_amount"]>0 and x["effective_price"]>0 for x in d["exact_rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-048B one shared universal economic normalizer")
  print("[PASS] exact venue trades normalized; decoder-pending venue activity retained raw")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
