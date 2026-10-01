import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_012_native_block_shape_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  print("[SIGNATURE]",d["signature"]);print("[KWARGS]",json.dumps(d["kwargs"],sort_keys=True))
  print("[OK]",d["ok"])
  if d.get("shape"):print("[SHAPE]",json.dumps(d["shape"],sort_keys=True))
  if d.get("error"):print("[ERROR]",d["error"])
  if not d["ok"]:self.fail("NATIVE_FINALIZED_BLOCK_PROBE_FAILED")
  print("[PASS] SULS-012 native finalized-block physical shape probe")
if __name__=="__main__":unittest.main()
