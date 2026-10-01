import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_017_live_native_transaction_program_scan import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_scan(self):
  p,d=write(ROOT)
  print("[HEAD_SLOT]",d["head_slot"]);print("[BLOCK_COUNT]",d["block_count"]);print("[TRANSACTION_COUNT]",d["transaction_count"])
  seen=sum(bool(x["program_ids"]) for x in d["rows"]);print("[ROWS_WITH_PROGRAM_IDS]",seen)
  for x in d["rows"][:20]:print("[TX]",json.dumps(x,sort_keys=True))
  if d["transaction_count"]==0:self.fail("NO_NATIVE_TRANSACTIONS")
  if seen==0:self.fail("NO_PROGRAM_IDS_EXTRACTED")
  print("[PASS] SULS-017 live native transaction/program scan")
if __name__=="__main__":unittest.main()
