from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
M=S/"qarb_062a_mriya_six_dex_router.py"
M.write_text("""from __future__ import annotations
import json
from pathlib import Path
DEX=Path("runtime_state/qseries/qarb_clean_bot/mriya_dex_instruction_accounts.json")
BIND=Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_active_bindings.json")
ALIASES={"PUMP_SWAP":"PUMPSWAP","METEORA_DLMM":"METEORA_DLMM","RAYDIUM_CPMM":"RAYDIUM_CPMM","METEORA_DAMM":"METEORA_DAMM_V2","METEORA_DAMM_V2":"METEORA_DAMM_V2","RAYDIUM_CLMM":"RAYDIUM_CLMM","ORCA":"ORCA_WHIRLPOOL","ORCA_WHIRLPOOL":"ORCA_WHIRLPOOL"}
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
def _load(p):
 try:return json.loads(Path(p).read_text(encoding="utf-8"))
 except Exception:return {}
def _rows(x):
 if isinstance(x,list):return x
 if isinstance(x,dict):
  for k in ("rows","instructions","bindings","tokens","items"):
   if isinstance(x.get(k),list):return x[k]
  return [v for v in x.values() if isinstance(v,dict)]
 return []
def context(root,token):
 root=Path(root);venues=set();last_age=None;touches=0
 for r in _rows(_load(root/DEX)):
  if token in (r.get("mints") or []):
   v=ALIASES.get(str(r.get("venue") or ""))
   if v:venues.add(v)
 for r in _rows(_load(root/BIND)):
  if str(r.get("token") or r.get("mint") or "")==token:
   last_age=r.get("last_age",r.get("age_last",r.get("last_age_s")));touches=int(r.get("touches") or 0)
 return {"token":token,"venues":sorted(venues),"mriya_age_s":last_age,"touches":touches,"seen":bool(venues or last_age is not None)}
def route(root,state):
 out={};hot=0
 for token in state.get("eps",{}):
  x=context(root,token);out[token]=x;hot+=int(x["seen"])
 return {"tokens":len(out),"mriya_overlap":hot,"rows":out,"execution_authority":False}
""",encoding="utf-8")
T=R/"test_qarb_062a_mriya_six_dex_router.py"
T.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062a_mriya_six_dex_router as q
class T(unittest.TestCase):
 def test_aliases(self):
  for x in ("PUMPSWAP","METEORA_DLMM","RAYDIUM_CPMM","METEORA_DAMM_V2","RAYDIUM_CLMM","ORCA_WHIRLPOOL"):self.assertIn(x,q.ALIASES.values())
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
for x in (M,T):py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-062A Mriya six-DEX router installed")
print("[ROUTER] existing Mriya evidence -> six normalized venue valves")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")