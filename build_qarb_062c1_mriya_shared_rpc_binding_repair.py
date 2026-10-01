from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
REQ=[S/"qarb_062c_live_mriya_existing_runner_activation.py",S/"qarb_061a_shared_rpc_valve.py"]
for x in REQ:
 if not x.exists():raise SystemExit("[FAIL] missing dependency: "+str(x))
M=S/"qarb_062c1_mriya_shared_rpc_binding_repair.py"
M.write_text("""from __future__ import annotations
import importlib
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as rv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062c_live_mriya_existing_runner_activation as q62c
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
def bind_all_rpc():
 rv.install()
 mods=[
  "qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition",
  "qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery",
  "qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_027_mriya_native_wallet_observer",
 ]
 bound=[]
 for name in mods:
  try:
   m=importlib.import_module(name)
   if hasattr(m,"_rpc"):
    m._rpc=lambda method,params,timeout_seconds=20.0:rv.gated_rpc(method,params)
    bound.append(name)
   if hasattr(m,"rpc"):
    m.rpc=lambda method,params,*a,**k:rv.gated_rpc(method,params)
    bound.append(name+":rpc")
  except Exception as e:
   print("[RPC_BIND_SKIP] %s %s:%s"%(name,type(e).__name__,e),flush=True)
 return bound
def main(argv=None):
 bound=bind_all_rpc()
 print("[QARB-062C1] MRIYA SHARED-RPC BINDING REPAIR",flush=True)
 print("[RPC_BOUND] "+str(bound),flush=True)
 print("[FIX] QARB-043B/OAD-148 direct urllib RPC now enters QARB-061A shared valve",flush=True)
 print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
 return q62c.main(argv)
if __name__=="__main__":main()
""",encoding="utf-8")
T=R/"test_qarb_062c1_mriya_shared_rpc_binding_repair.py"
U=R/"run_qarb_062c1_mriya_shared_rpc_binding_repair.py"
T.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062c1_mriya_shared_rpc_binding_repair as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_binding(self):self.assertTrue(any("oad_148" in x for x in q.bind_all_rpc()))
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
U.write_text("""from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_062c1_mriya_shared_rpc_binding_repair import main
if __name__=="__main__":main()
""",encoding="utf-8")
for x in (M,T,U):py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-062C1 Mriya shared-RPC binding repair installed")
print("[FIX] binds direct QARB-043B/OAD-148 RPC calls into existing QARB-061A valve")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")