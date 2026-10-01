import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_018_native_pool_birth_candidate_decoder import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_decode(self):
  p,d=write(ROOT)
  print("[TRANSACTION_COUNT]",d["transaction_count"]);print("[CANDIDATE_COUNT]",d["candidate_count"])
  for x in d["candidates"][:20]:print("[POOL_BIRTH_CANDIDATE]",json.dumps(x,sort_keys=True))
  print("[SCOPE]",d["scope"])
  print("[PASS] SULS-018 native pool-birth candidate decoder")
if __name__=="__main__":unittest.main()
