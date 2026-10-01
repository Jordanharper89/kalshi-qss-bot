import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_001_universal_launcher_registry import write,classify
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_exact_precedence(self):
  p,d=write(ROOT)
  checks={
   "pumpfun":"PUMPFUN","pumpswap":"PUMPSWAP",
   "raydium_cpmm":"RAYDIUM_CPMM","cpmm":"RAYDIUM_CPMM",
   "raydium_clmm":"RAYDIUM_CLMM","clmm":"RAYDIUM_CLMM",
   "raydium_amm":"RAYDIUM_AMM","raydium_v4":"RAYDIUM_AMM","raydium":"RAYDIUM_AMM",
   "meteora_dlmm":"METEORA_DLMM","meteora_damm":"METEORA_DAMM","meteora":"METEORA",
   "moonshot":"MOONSHOT","stonk.fun":"STONK_FUN","letsbonk":"BONK_FUN",
   "orca_whirlpool":"ORCA_WHIRLPOOL","future_launcher_xyz":"UNKNOWN_PROGRAM"}
  for raw,expected in checks.items():
   got=classify(raw)
   print("[CLASSIFY]",raw,"->",got)
   self.assertEqual(got,expected)
  self.assertTrue(d["unknown_program_admission"])
  self.assertFalse(d["execution_authority"])
  print("[UNKNOWN_PROGRAM_ADMISSION]",d["unknown_program_admission"])
  print("[PASS] SULS-001C exact launcher-family precedence")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
