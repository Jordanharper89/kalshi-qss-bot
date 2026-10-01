from __future__ import annotations
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
