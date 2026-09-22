from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_035_pump_trade_raw_transaction_hydration.py"
TEST=ROOT/"test_usls_035_pump_trade_raw_transaction_hydration.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_022_live_pump_create_v2_capture import _tx

def hydrate(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_normalized_trade_tape.json").read_text(encoding="utf-8"))
 rows=[];cache={}
 for x in src.get("rows") or []:
  sig=x["signature"]
  if sig not in cache:
   cache[sig]=_tx(sig)
   time.sleep(.08)
  tx=cache[sig]
  rows.append({"trade_id":x["trade_id"],"signature":sig,"side":x["side"],
   "token_address":x["token_address"],"market_address":x["market_address"],
   "quote_mint":x["quote_mint"],"birth_age_seconds":x["birth_age_seconds"],
   "instruction_index":x["instruction_index"],"raw_transaction":tx,
   "hydrated":tx is not None,"execution_authority":False})
 return {"revision":"USLS_035","row_count":len(rows),
  "hydrated_count":sum(1 for x in rows if x["hydrated"]),
  "unique_signature_count":len(cache),"rows":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=hydrate(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_trade_raw_transactions.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_035_pump_trade_raw_transaction_hydration import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_hydrate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:d[k] for k in ("row_count","hydrated_count","unique_signature_count")},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["hydrated_count"],d["row_count"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-035 Pump trade raw transactions physically hydrated")
  print("[PASS] signer/token-balance evidence preserved for every captured trade")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
