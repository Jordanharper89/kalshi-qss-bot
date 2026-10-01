from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_007_native_solana_capability_audit.py";TEST=ROOT/"test_suls_007_native_solana_capability_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import ast,json
TOKENS=("websocket","subscribe","logsSubscribe","programSubscribe","blockSubscribe","slotSubscribe","signatureSubscribe","getBlock","getTransaction","getSignaturesForAddress","program_id","programid","instruction","transaction")
def audit(root):
 base=root/"qseries_v2/oracle_adapters/independent";rows=[]
 for p in base.glob("oad_*solana*.py"):
  text=p.read_text(encoding="utf-8",errors="ignore");low=text.lower();hits=sorted({t for t in TOKENS if t.lower() in low});funcs=[]
  try: funcs=[n.name for n in ast.walk(ast.parse(text)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
  except Exception: pass
  if hits: rows.append({"file":str(p.relative_to(root)),"hits":hits,"functions":funcs[:80]})
 return {"revision":"SULS_007","files_with_native_signals":len(rows),"rows":rows,"execution_authority":False}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_capability_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_007_native_solana_capability_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);print("[FILES_WITH_NATIVE_SIGNALS]",d["files_with_native_signals"])
  for r in d["rows"]: print("[NATIVE_FILE]",json.dumps(r,sort_keys=True))
  if d["files_with_native_signals"]==0:self.fail("NO_NATIVE_SOLANA_CAPABILITY_EVIDENCE")
  print("[PASS] SULS-007 native Solana capability audit")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name)