from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"

REQ=[
 S/"qarb_062c1_mriya_shared_rpc_binding_repair.py",
 S/"qarb_061d_subscription_cap_aware_ws_valves.py",
 S/"qarb_060b2_single_hydration_cached_runner_cutover.py",
]
for x in REQ:
 if not x.exists():raise SystemExit("[FAIL] missing dependency: "+str(x))

U=R/"run_qarb_live_paper_runtime.py"

U.write_text("""from __future__ import annotations
import asyncio,threading
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062c1_mriya_shared_rpc_binding_repair as q62c1
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062c_live_mriya_existing_runner_activation as q62c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q61d
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b2_single_hydration_cached_runner_cutover as q60b2
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_062b_mriya_paper_outcome_lineage as ml

EXECUTION_AUTHORITY=False
PAPER_ONLY=True

def main():
 root=Path.cwd()
 bound=q62c1.bind_all_rpc()
 q62c.STOP=False
 state,cap=q60b2.prepare_once(root)

 def cached_prepare(_root):return state

 q60b.m.prepare=cached_prepare
 q60b.m.capability=q60b.extended_capability
 q60b.p._process_event=q60b.extended_process
 q60b.m._shards=q61d.capped_valves
 q60b.p.m._shards=q61d.capped_valves
 q60b.p._worker=q61d.staggered_worker
 q60b.p.SimulationLane=ml.MriyaPaperLane

 feed=threading.Thread(target=q62c._feed,args=(20.0,),daemon=True)
 feed.start()

 print("[QARB-063] CONTINUOUS LIVE PAPER ARBITRAGE RUNTIME",flush=True)
 print("[RPC_BOUND] "+str(bound),flush=True)
 print("[LIVE] Mriya + six DEX valves + existing persistent runner",flush=True)
 print("[RUNTIME] unbounded; stop manually with Ctrl+C",flush=True)
 print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)

 try:
  return asyncio.run(q60b.p.serve(root,None))
 except KeyboardInterrupt:
  print("\\n[STOP] operator Ctrl+C",flush=True)
 finally:
  q62c.STOP=True

if __name__=="__main__":
 main()
""",encoding="utf-8")

py_compile.compile(str(U),doraise=True)

print("[PASS] QARB-063 continuous live paper launcher installed")
print("[RUNNER] existing persistent runtime; no time limit")
print("[STOP] Ctrl+C")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")