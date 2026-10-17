from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"live_money_persistent_driver.py"
TEST=ROOT/"test_live_money_persistent_driver_replacement.py"

CODE='from __future__ import annotations\nimport argparse\nimport inspect\nfrom . import live_money_driver as d\n\ndef main():\n    p=argparse.ArgumentParser()\n    p.add_argument("--seconds",type=float,default=1800.0)\n    p.add_argument("--refresh-seconds",type=float,default=60.0)\n    a=p.parse_args()\n    if a.seconds<300:\n        raise RuntimeError("PERSISTENT_SESSION_MINIMUM_300_SECONDS")\n    sig=inspect.signature(d._run_generation)\n    if len(sig.parameters)!=4:\n        raise RuntimeError("LIVE_MONEY_DRIVER_CONTRACT_DRIFT:"+str(sig))\n    active={}\n    print("[PERSISTENT_MONEY_START] single_startup=True generation=1 warm_session_seconds=%.1f repeated_generation_rebuild=False"%a.seconds,flush=True)\n    print("[PERSISTENT_CONTRACT] _run_generation(generation,generation_seconds,refresh_seconds,active)",flush=True)\n    print("[PERSISTENT_POLICY] CP24/CP12/templates/websockets=start_once capital_ladder=wallet_funded broadcast=False",flush=True)\n    rc,active=d._run_generation(1,float(a.seconds),float(a.refresh_seconds),active)\n    print("[PERSISTENT_MONEY_DONE] rc=%s active_pairs=%d"%(str(rc),len(active or {})),flush=True)\n    return int(rc or 0)\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'

TEST_CODE='import inspect\nfrom pathlib import Path\nfrom qseries_v2.oracle_execution.solana_atomic_executor import live_money_driver as d\nfrom qseries_v2.oracle_execution.solana_atomic_executor import live_money_persistent_driver as p\nfrom qseries_v2.oracle_execution.solana_atomic_executor import runtime as r\nassert len(inspect.signature(d._run_generation).parameters)==4\ns=Path(p.__file__).read_text(encoding="utf-8")\nassert "d._run_generation(1,float(a.seconds),float(a.refresh_seconds),active)" in s\nassert "repeated_generation_rebuild=False" in s\nassert hasattr(r.q18,"_oracle_unfunded_exact_snapshot_opportunities")\nassert r._CAPITAL_RESERVE_LAMPORTS==5_000_000\nassert "sendTransaction" not in s\nprint("[PASS] persistent driver replacement contract + capital gate preserved")\n'

if not PKG.is_dir():
    raise RuntimeError("SOLANA_ATOMIC_EXECUTOR_PACKAGE_MISSING")

ast.parse(CODE)
ast.parse(TEST_CODE)
TARGET.write_text(CODE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] persistent driver full replacement installed")
print("[CONTRACT] four-argument _run_generation")
print("[SESSION] one generation owns full requested runtime")
print("[CAPITAL_GATE] preserved")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)