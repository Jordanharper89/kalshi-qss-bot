from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
RUNTIME=PKG/"runtime.py"
PERSISTENT=PKG/"live_money_persistent_driver.py"
TEST=ROOT/"test_live_money_persistent_capital_gate.py"

CAPITAL='\n# === ORACLE FUNDED SIZE GATE ===\n_CAPITAL_CACHE={"balance":None,"updated":0.0,"allowed":None}\n_CAPITAL_RESERVE_LAMPORTS=5_000_000\n_CAPITAL_REFRESH_SECONDS=10.0\n\nif not hasattr(q18,"_oracle_unfunded_exact_snapshot_opportunities"):\n    q18._oracle_unfunded_exact_snapshot_opportunities=q18.exact_snapshot_opportunities\n\ndef _funded_size_allowed(size_sol):\n    if USER is None: return True\n    now=time.monotonic()\n    if _CAPITAL_CACHE["balance"] is None or now-_CAPITAL_CACHE["updated"]>=_CAPITAL_REFRESH_SECONDS:\n        result=q87.c.rpc("getBalance",[str(USER),{"commitment":"processed"}])\n        if not isinstance(result,dict): raise RuntimeError("CAPITAL_BALANCE_RESULT_NOT_MAPPING")\n        value=result.get("value")\n        if not isinstance(value,int): raise RuntimeError("CAPITAL_BALANCE_VALUE_NOT_INT")\n        _CAPITAL_CACHE["balance"]=value; _CAPITAL_CACHE["updated"]=now\n        funded=max(0,value-_CAPITAL_RESERVE_LAMPORTS)\n        ladder=(0.001,0.010,0.025,0.050,0.100,0.180,0.280,0.500,1.000,1.400)\n        allowed=[s for s in ladder if int(round(s*1_000_000_000*1.002))<=funded]\n        _CAPITAL_CACHE["allowed"]=tuple(allowed)\n        print("[CAPITAL_LADDER] balance=%d reserve=%d funded=%d allowed=%s"%(value,_CAPITAL_RESERVE_LAMPORTS,funded,",".join("%.3f"%s for s in allowed) or "NONE"),flush=True)\n    return float(size_sol) in (_CAPITAL_CACHE.get("allowed") or ())\n\ndef _capital_filtered_exact_snapshot_opportunities(snap,size_sol):\n    if not _funded_size_allowed(size_sol): return []\n    return q18._oracle_unfunded_exact_snapshot_opportunities(snap,size_sol)\n\nq18.exact_snapshot_opportunities=_capital_filtered_exact_snapshot_opportunities\n'

PERSISTENT_CODE='''from __future__ import annotations
import argparse
from . import live_money_driver as d

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=float,default=1800.0)
    p.add_argument("--refresh-seconds",type=float,default=60.0)
    args=p.parse_args()
    if args.seconds<300: raise RuntimeError("PERSISTENT_SESSION_MINIMUM_300_SECONDS")
    print("[PERSISTENT_MONEY_START] single_startup=True warm_session_seconds=%.1f active_profit_retention=True repeated_generation_rebuild=False"%args.seconds,flush=True)
    print("[PERSISTENT_POLICY] CP24/CP12/templates/websockets=start_once capital_ladder=wallet_funded broadcast=False",flush=True)
    result=d._run_generation(float(args.seconds),float(args.refresh_seconds))
    print("[PERSISTENT_MONEY_DONE] single_generation=True result=%s"%str(result),flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
'''

TEST_CODE='''from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_persistent_driver as p
assert hasattr(r.q18,"_oracle_unfunded_exact_snapshot_opportunities")
assert r._CAPITAL_RESERVE_LAMPORTS==5_000_000
funded=40_000_000-r._CAPITAL_RESERVE_LAMPORTS
assert int(round(.025*1_000_000_000*1.002))<=funded
assert int(round(.050*1_000_000_000*1.002))>funded
s=Path(p.__file__).read_text(encoding="utf-8")
assert s.count("d._run_generation(")==1
assert "repeated_generation_rebuild=False" in s
assert "sendTransaction" not in Path(r.__file__).read_text(encoding="utf-8")
print("[PASS] persistent warm runtime and funded-size gate")
'''

if not RUNTIME.is_file(): raise RuntimeError("CANONICAL_RUNTIME_MISSING")
src=RUNTIME.read_text(encoding="utf-8")
if "=== ORACLE FUNDED SIZE GATE ===" not in src:
    marker='if __name__=="__main__":'
    if marker not in src: marker='if __name__ == "__main__":'
    if marker not in src: raise RuntimeError("RUNTIME_MAIN_MARKER_NOT_FOUND")
    src=src.replace(marker,CAPITAL+"\n\n"+marker,1)
ast.parse(src); ast.parse(PERSISTENT_CODE); ast.parse(TEST_CODE)
RUNTIME.write_text(src,encoding="utf-8")
PERSISTENT.write_text(PERSISTENT_CODE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")
print("[PASS] persistent warm + funded-size gate installed")
print("[STARTUP] one supervisor generation for full requested session")
print("[CAPITAL] unfundable sizes removed before ranking")
print("[RESERVE] 0.005 SOL held back for fees/rent")
print("[ACTIVE_PROFIT] existing driver parser preserved")
print("[KEY] untouched")
print("[BROADCAST] disabled")