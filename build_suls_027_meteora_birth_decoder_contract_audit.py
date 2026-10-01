from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_027_meteora_birth_decoder_contract_audit.py"
TEST=ROOT/"test_suls_027_meteora_birth_decoder_contract_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import inspect,json
TARGETS=(
 "qseries_v2.oracle_adapters.independent.oad_336_solana_pump_meteora_market_behavior_decoder",
 "qseries_v2.oracle_adapters.independent.oad_355_solana_final_economic_behavior_decoder",
 "qseries_v2.oracle_adapters.independent.oad_353_solana_final_verified_economic_program_expansion",
)
def audit():
 rows=[]
 for name in TARGETS:
  try:
   m=__import__(name,fromlist=["*"]);src=inspect.getsource(m);funcs={}
   for n,v in vars(m).items():
    if callable(v) and not n.startswith("_"):
     try:funcs[n]=str(inspect.signature(v))
     except Exception:funcs[n]="?"
   rows.append({"module":name,"functions":funcs,"source_excerpt":src[:16000]})
  except Exception as e:rows.append({"module":name,"error":f"{type(e).__name__}: {e}"})
 return {"revision":"SULS_027","modules":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=audit();p=root/"runtime_state/solana_opportunities/launch_surveillance/meteora_birth_decoder_contracts.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_027_meteora_birth_decoder_contract_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);good=[x for x in d["modules"] if x.get("functions")]
  print("[CALLABLE_MODULES]",len(good))
  for x in d["modules"]:
   print("[MODULE]",x["module"])
   if x.get("functions"):print("[FUNCTIONS]",json.dumps(x["functions"],sort_keys=True))
   if x.get("source_excerpt"):print("[SOURCE_EXCERPT]");print(x["source_excerpt"])
  if not good:self.fail("NO_METEORA_DECODER_CONTRACTS")
  print("[PASS] SULS-027 Meteora birth decoder contract audit")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")