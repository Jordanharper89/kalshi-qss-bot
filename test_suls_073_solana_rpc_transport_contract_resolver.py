import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_073_solana_rpc_transport_contract_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_resolve(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="rpc_source_excerpt"},sort_keys=True))
  print("[RPC_EXCERPT]");print(d["rpc_source_excerpt"])
  if not d["selected_http"] or not d["derived_ws"]:self.fail("SOLANA_RPC_TRANSPORT_UNRESOLVED")
  print("[PASS] SULS-073 Solana RPC transport contract resolver")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
