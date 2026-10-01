from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_001_universal_launcher_registry.py"
TEST=ROOT/"test_suls_001b_universal_launcher_registry_expansion.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

REGISTRY=(
 {"family":"PUMPFUN","aliases":("pumpfun","pump.fun"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"PUMPSWAP","aliases":("pumpswap","pump_swap"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"RAYDIUM_CPMM","aliases":("raydium_cpmm","cpmm"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"RAYDIUM_AMM","aliases":("raydium_amm","raydium_v4","raydium"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"RAYDIUM_CLMM","aliases":("raydium_clmm","clmm"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"METEORA_DLMM","aliases":("meteora_dlmm","dlmm"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"METEORA_DAMM","aliases":("meteora_damm","damm"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"METEORA","aliases":("meteora",),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"MOONSHOT","aliases":("moonshot",),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"STONK_FUN","aliases":("stonk.fun","stonk_fun","stonkfun"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"BONK_FUN","aliases":("bonk.fun","bonk_fun","letsbonk","lets_bonk"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"ORCA_WHIRLPOOL","aliases":("orca_whirlpool","whirlpool","orca"),"program_ids":(),"program_ids_physically_verified":False},
)

def classify(dex_id=None, program_hint=None, source_hint=None):
 hay=" ".join(str(x or "").strip().lower() for x in (dex_id,program_hint,source_hint))
 for row in REGISTRY:
  if any(a in hay for a in row["aliases"]):
   return row["family"]
 return "UNKNOWN_PROGRAM"

def build():
 return {
  "revision":"SULS_001B",
  "registry":[dict(x) for x in REGISTRY],
  "families":[x["family"] for x in REGISTRY]+["UNKNOWN_PROGRAM"],
  "unknown_program_admission":True,
  "observation_policy":"OBSERVE_FIRST_CLASSIFY_WHEN_KNOWN_NEVER_DROP_UNKNOWN",
  "program_ids_physically_verified":False,
  "execution_authority":False,
  "read_only":True,
 }

def write(root):
 d=build()
 p=root/"runtime_state/solana_opportunities/launch_surveillance/launcher_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
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
"""

def main():
 print("="*116)
 print(" SULS-001B UNIVERSAL SOLANA LAUNCHER / POOL-FAMILY REGISTRY")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replaces narrow SULS-001 with universal known-family + UNKNOWN_PROGRAM admission")

if __name__=="__main__":
 main()
