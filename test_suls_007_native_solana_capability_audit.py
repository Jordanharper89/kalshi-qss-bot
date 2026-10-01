import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_007_native_solana_capability_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);print("[FILES_WITH_NATIVE_SIGNALS]",d["files_with_native_signals"])
  for r in d["rows"]: print("[NATIVE_FILE]",json.dumps(r,sort_keys=True))
  if d["files_with_native_signals"]==0:self.fail("NO_NATIVE_SOLANA_CAPABILITY_EVIDENCE")
  print("[PASS] SULS-007 native Solana capability audit")
if __name__=="__main__":unittest.main()
