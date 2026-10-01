import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_001_universal_launcher_registry import write,classify

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT)
  self.assertFalse(d["execution_authority"])
  self.assertTrue(d["unknown_program_admission"])
  checks={
   "pumpfun":"PUMPFUN",
   "pumpswap":"PUMPSWAP",
   "raydium_cpmm":"RAYDIUM_CPMM",
   "raydium_clmm":"RAYDIUM_CLMM",
   "raydium_v4":"RAYDIUM_AMM",
   "meteora_dlmm":"METEORA_DLMM",
   "meteora_damm":"METEORA_DAMM",
   "moonshot":"MOONSHOT",
   "stonk.fun":"STONK_FUN",
   "letsbonk":"BONK_FUN",
   "orca_whirlpool":"ORCA_WHIRLPOOL",
   "future_launcher_xyz":"UNKNOWN_PROGRAM",
  }
  for raw,expected in checks.items():
   got=classify(raw)
   print("[CLASSIFY]",raw,"->",got)
   self.assertEqual(got,expected)
  print("[FAMILIES]",json.dumps(d["families"]))
  print("[OBSERVATION_POLICY]",d["observation_policy"])
  print("[UNKNOWN_PROGRAM_ADMISSION]",d["unknown_program_admission"])
  print("[PASS] SULS-001B universal launcher registry expansion")
  print("[SCOPE] Program IDs remain unclaimed until physically resolved from live/native evidence")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
