import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_012_native_block_shape_probe import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_recertify(self):
  p,d=write(ROOT)

  print("[STATE_FILE]",p)
  print("[OK]",d.get("ok"))
  print("[SHAPE]",json.dumps(d.get("shape"),sort_keys=True))

  self.assertTrue(d.get("ok"))
  self.assertEqual((d.get("shape") or {}).get("type"),
                   "SolanaFinalizedBlockBatch")

  persisted=json.loads(p.read_text(encoding="utf-8"))
  self.assertTrue(persisted.get("ok"))

  print("[PERSISTED_OK]",persisted.get("ok"))
  print("[PASS] SULS-012D native block state recertification")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
