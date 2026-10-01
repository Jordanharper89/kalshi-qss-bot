from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_016_native_program_contract_resolver.py"
TEST=ROOT/"test_suls_016_native_program_contract_resolver.py"

MOD_TEXT=r"""from __future__ import annotations
import inspect,json
from pathlib import Path

MODULES=(
 "qseries_v2.oracle_adapters.independent.oad_333_solana_authoritative_program_identity_registry",
 "qseries_v2.oracle_adapters.independent.oad_339_solana_reconciled_program_identity_registry",
 "qseries_v2.oracle_adapters.independent.oad_343_solana_verified_recurring_program_identity_expansion",
 "qseries_v2.oracle_adapters.independent.oad_348_solana_verified_economic_program_expansion",
 "qseries_v2.oracle_adapters.independent.oad_353_solana_final_verified_economic_program_expansion",
)

def resolve():
 rows=[]
 for name in MODULES:
  try:
   m=__import__(name,fromlist=["*"])
   funcs={}
   for n,v in vars(m).items():
    if callable(v) and not n.startswith("_"):
     try: funcs[n]=str(inspect.signature(v))
     except Exception: funcs[n]="?"
   src=inspect.getsource(m)
   rows.append({"module":name,"functions":funcs,"source_excerpt":src[:12000]})
  except Exception as e:
   rows.append({"module":name,"error":f"{type(e).__name__}: {e}"})
 return {"revision":"SULS_016","modules":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=resolve();p=root/"runtime_state/solana_opportunities/launch_surveillance/native_program_contracts.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_016_native_program_contract_resolver import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contracts(self):
  p,d=write(ROOT)
  good=[x for x in d["modules"] if x.get("functions")]
  print("[MODULES]",len(d["modules"]));print("[CALLABLE_MODULES]",len(good))
  for x in good:print("[PROGRAM_MODULE]",x["module"],json.dumps(x["functions"],sort_keys=True))
  if not good:self.fail("NO_PROGRAM_IDENTITY_CALLABLES")
  print("[PASS] SULS-016 native program contract resolver")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-016 NATIVE PROGRAM CONTRACT RESOLVER");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()