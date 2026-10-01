import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_063_native_expansion_return_shape_audit import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  print("[LIVE_ASSET]",d["asset_key"])
  print("[RETURN_TYPE]",d["return_type"])
  print("[RETURN_SHAPE]",json.dumps(d["shape"],sort_keys=True)[:12000])
  print("[PASS] OSI-063D native expansion return-shape audit")
  print("[TRADER] Exposes the exact live native pool object contract before the anchor parser is rebuilt")
  print("[SCOPE] Read-only shape audit; no PostgreSQL write and no guessed pool schema")

if __name__=="__main__":
 unittest.main()
