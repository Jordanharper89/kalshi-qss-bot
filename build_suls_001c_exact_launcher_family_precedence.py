from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_001_universal_launcher_registry.py"
TEST=ROOT/"test_suls_001c_exact_launcher_family_precedence.py"

MOD_TEXT=r"""from __future__ import annotations
import json,re

REGISTRY=(
 {"family":"RAYDIUM_CPMM","aliases":("raydium_cpmm","cpmm")},
 {"family":"RAYDIUM_CLMM","aliases":("raydium_clmm","clmm")},
 {"family":"RAYDIUM_AMM","aliases":("raydium_amm","raydium_v4","raydium")},
 {"family":"METEORA_DLMM","aliases":("meteora_dlmm","dlmm")},
 {"family":"METEORA_DAMM","aliases":("meteora_damm","damm")},
 {"family":"METEORA","aliases":("meteora",)},
 {"family":"PUMPFUN","aliases":("pumpfun","pump.fun")},
 {"family":"PUMPSWAP","aliases":("pumpswap","pump_swap")},
 {"family":"MOONSHOT","aliases":("moonshot",)},
 {"family":"STONK_FUN","aliases":("stonk.fun","stonk_fun","stonkfun")},
 {"family":"BONK_FUN","aliases":("bonk.fun","bonk_fun","letsbonk","lets_bonk")},
 {"family":"ORCA_WHIRLPOOL","aliases":("orca_whirlpool","whirlpool","orca")},
)

def _norm(v):
 s=str(v or "").strip().lower()
 s=re.sub(r"[^a-z0-9]+","_",s).strip("_")
 return s

def classify(dex_id=None,program_hint=None,source_hint=None):
 vals={_norm(x) for x in (dex_id,program_hint,source_hint) if str(x or "").strip()}
 for row in REGISTRY:
  aliases={_norm(a) for a in row["aliases"]}
  if vals & aliases:return row["family"]
 return "UNKNOWN_PROGRAM"

def build():
 return {"revision":"SULS_001C",
  "registry":[{"family":x["family"],"aliases":list(x["aliases"]),
               "program_ids":[],"program_ids_physically_verified":False} for x in REGISTRY],
  "families":[x["family"] for x in REGISTRY]+["UNKNOWN_PROGRAM"],
  "unknown_program_admission":True,
  "observation_policy":"OBSERVE_FIRST_CLASSIFY_WHEN_KNOWN_NEVER_DROP_UNKNOWN",
  "program_ids_physically_verified":False,
  "execution_authority":False,"read_only":True}

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
"""

def main():
 print("="*116)
 print(" SULS-001C EXACT UNIVERSAL LAUNCHER-FAMILY PRECEDENCE")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Retires substring classifier; exact normalized family aliases only")

if __name__=="__main__":
 main()
