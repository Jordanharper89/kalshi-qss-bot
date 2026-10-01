from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_001_universal_launcher_registry.py"
TEST=ROOT/"test_suls_001_universal_launcher_registry.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

REGISTRY=(
 {"family":"PUMPFUN","aliases":("pumpfun",),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"PUMPSWAP","aliases":("pumpswap",),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"RAYDIUM","aliases":("raydium","raydium_cpmm","raydium_amm"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"METEORA","aliases":("meteora","meteora_dlmm","meteora_damm"),"program_ids":(),"program_ids_physically_verified":False},
 {"family":"MOONSHOT","aliases":("moonshot",),"program_ids":(),"program_ids_physically_verified":False},
)

def classify(dex_id):
 s=str(dex_id or "").strip().lower()
 for row in REGISTRY:
  if any(a in s for a in row["aliases"]):return row["family"]
 return "OTHER"

def build():
 return {"revision":"SULS_001","registry":[dict(x) for x in REGISTRY],
  "families":[x["family"] for x in REGISTRY]+["OTHER"],
  "execution_authority":False,"read_only":True}

def write(root):
 d=build();p=root/"runtime_state/solana_opportunities/launch_surveillance/launcher_registry.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_001_universal_launcher_registry import write,classify
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registry(self):
  p,d=write(ROOT);self.assertFalse(d["execution_authority"])
  self.assertEqual(classify("pumpfun"),"PUMPFUN")
  self.assertEqual(classify("pumpswap"),"PUMPSWAP")
  self.assertEqual(classify("raydium"),"RAYDIUM")
  self.assertEqual(classify("meteora"),"METEORA")
  self.assertEqual(classify("moonshot"),"MOONSHOT")
  print("[FAMILIES]",json.dumps(d["families"]))
  print("[PASS] SULS-001 universal launcher registry")
  print("[SCOPE] Program IDs remain unclaimed until physically resolved")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-001 UNIVERSAL SOLANA LAUNCHER REGISTRY");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
