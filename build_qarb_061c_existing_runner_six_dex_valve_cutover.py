from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
REQ=[S/"qarb_061a_shared_rpc_valve.py",S/"qarb_061b_two_ws_valves_paper_lane.py",S/"qarb_060b2_single_hydration_cached_runner_cutover.py"]
for d in REQ:
    if not d.exists(): raise SystemExit("[FAIL] missing dependency: "+str(d))
M=S/"qarb_061c_existing_runner_six_dex_valve_cutover.py"
M.write_text("""from __future__ import annotations
import argparse,asyncio,json,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as rv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061b_two_ws_valves_paper_lane as wv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b2_single_hydration_cached_runner_cutover as q60b2
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
STARTUP_COOLDOWN_SECONDS=3.0
def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=30.0);a=ap.parse_args(argv)
    root=Path.cwd();rv.install();wv.install()
    q60b.c.rpc=rv.gated_rpc
    state,cap=q60b2.prepare_once(root)
    def cached_prepare(_root): return state
    q60b.m.prepare=cached_prepare;q60b.m.capability=q60b.extended_capability;q60b.p._process_event=q60b.extended_process
    q60b.m._shards=wv.two_valves;q60b.p.m._shards=wv.two_valves;wv.install()
    valves={"PUMPSWAP":"preg","METEORA_DLMM":"preg","RAYDIUM_CPMM":"creg","METEORA_DAMM_V2":"xreg:DAMM","RAYDIUM_CLMM":"xreg:CLMM","ORCA_WHIRLPOOL":"xreg:ORCA"}
    print("[QARB-061C] SIX-DEX VALVES -> EXISTING PERSISTENT RUNNER",flush=True)
    print("[VALVES] "+json.dumps(valves,sort_keys=True),flush=True)
    print("[CUTOVER] accounts=%d priced_tokens=%d extension_registry=%d"%(len(state["addresses"]),len(state["eps"]),len(state.get("xreg",{}))),flush=True)
    print("[CAPABILITY] "+json.dumps(cap,sort_keys=True),flush=True)
    print("[WS_LANE] connections=%d"%len(wv.two_valves(state["addresses"])),flush=True)
    print("[RPC_LANE] serialized_gap>=%.2fs"%rv.MIN_RPC_GAP_SECONDS,flush=True)
    print("[SIM_LANE] PAPER_ONLY no simulateTransaction RPC",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",flush=True)
    time.sleep(STARTUP_COOLDOWN_SECONDS)
    result=asyncio.run(q60b.p.serve(root,a.seconds))
    print("[TRANSPORT_RESULT] rpc_calls=%d caught_429=%d"%(rv.RPC_CALLS,rv.RPC_429),flush=True)
    return result
if __name__=="__main__":main()
""",encoding="utf-8")
T=R/"test_qarb_061c_existing_runner_six_dex_valve_cutover.py"
U=R/"run_qarb_061c_existing_runner_six_dex_valve_cutover.py"
T.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061c_existing_runner_six_dex_valve_cutover as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
if __name__=="__main__": unittest.main(verbosity=2)
""",encoding="utf-8")
U.write_text("""from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_061c_existing_runner_six_dex_valve_cutover import main
if __name__=="__main__":main()
""",encoding="utf-8")
for x in (M,T,U): py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-061C six-DEX existing-runner cutover installed")
print("[ARCH] PumpSwap + DLMM + CPMM + DAMM V2 + CLMM + Orca -> one existing runner")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")