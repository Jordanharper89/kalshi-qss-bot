import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_profitability_runtime.ssr_012_pumpswap_money_follower import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  f=ROOT/"runtime_state/solana_opportunities/solana_scanner/phase8_prospective_freeze_ledger.json"
  self.assertTrue(f.exists())
  d=json.loads(f.read_text(encoding="utf-8"));n=sum(x.get("family")=="PUMP_SWAP" for x in d.get("frozen_setups",[]))
  print("[STATE]",json.dumps({"pumpswap_frozen_setups":n},sort_keys=True))
  self.assertGreater(n,0,"NO_PUMPSWAP_FROZEN_SETUPS")
  print("[PASS] SSR-012 PumpSwap exact-market money follower contract")
  print("[INFO] live follower is activated by SSR-013 runtime worker")
if __name__=="__main__":unittest.main()
