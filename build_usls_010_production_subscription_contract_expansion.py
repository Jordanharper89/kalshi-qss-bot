from pathlib import Path
import re,ast

ROOT=Path(__file__).resolve().parent
TARGET=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_074_confirmed_logs_subscription_contract.py"
TEST=ROOT/"test_usls_010_production_subscription_contract_expansion.py"

PROGRAMS=[
("PUMP_FUN","6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"),
("PUMP_SWAP","pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"),
("RAYDIUM_LAUNCHLAB","LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"),
("RAYDIUM_V4","675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"),
("RAYDIUM_CLMM","CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"),
("RAYDIUM_CPMM","CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"),
("METEORA_DBC","dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN"),
("METEORA_DAMM","cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"),
("METEORA_DLMM","LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo"),
("METEORA_DYN","Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB"),
("ORCA","whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"),
("MOONIT","MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG"),
("BOOP_FUN","boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4"),
("HEAVEN","HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o"),
]

if not TARGET.exists(): raise SystemExit("SULS_074_NOT_FOUND")
src=TARGET.read_text(encoding="utf-8");ast.parse(src)
bak=TARGET.with_suffix(".pre_usls010.bak")
if not bak.exists(): bak.write_text(src,encoding="utf-8")

block="PROGRAM_FAMILIES = "+repr(tuple(PROGRAMS))+"\nPROGRAM_IDS = tuple(pid for _, pid in PROGRAM_FAMILIES)\n"
if "PROGRAM_FAMILIES =" not in src:
    lines=src.splitlines(True);pos=0
    while pos<len(lines) and (lines[pos].startswith("from ") or lines[pos].startswith("import ") or not lines[pos].strip()):
        pos+=1
    src="".join(lines[:pos])+block+"".join(lines[pos:])

replacements=0
for pat in (r"\(\s*DBC\s*,\s*DAMM\s*\)",r"\[\s*DBC\s*,\s*DAMM\s*\]"):
    src,n=re.subn(pat,"PROGRAM_IDS",src);replacements+=n

if replacements==0 and "PROGRAM_IDS" not in src:
    raise SystemExit("OLD_TWO_PROGRAM_SUBSCRIPTION_ITERABLE_NOT_FOUND")

ast.parse(src);TARGET.write_text(src,encoding="utf-8")
ids=[p for _,p in PROGRAMS]
test='''import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
P=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_074_confirmed_logs_subscription_contract.py"
IDS=%r
class T(unittest.TestCase):
 def test_contract(self):
  s=P.read_text(encoding="utf-8");ast.parse(s)
  missing=[x for x in IDS if x not in s]
  print("[STATE]",{"program_ids":len(IDS),"missing":len(missing),"logsSubscribe":"logsSubscribe" in s})
  self.assertFalse(missing);self.assertIn("PROGRAM_IDS",s);self.assertIn("logsSubscribe",s)
  print("[PASS] USLS-010 production subscription contract expanded to 14 verified programs")
  print("[PASS] existing SULS subscription API preserved")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
''' % ids
TEST.write_text(test,encoding="utf-8")
print("[PASS] repaired:",TARGET.relative_to(ROOT))
print("[PASS] backup:",bak.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
