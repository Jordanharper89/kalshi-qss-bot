import inspect
from pathlib import Path
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_driver as d
from qseries_v2.oracle_execution.solana_atomic_executor import live_money_persistent_driver as p
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
assert len(inspect.signature(d._run_generation).parameters)==4
s=Path(p.__file__).read_text(encoding="utf-8")
assert "d._run_generation(1,float(a.seconds),float(a.refresh_seconds),active)" in s
assert "repeated_generation_rebuild=False" in s
assert hasattr(r.q18,"_oracle_unfunded_exact_snapshot_opportunities")
assert r._CAPITAL_RESERVE_LAMPORTS==5_000_000
assert "sendTransaction" not in s
print("[PASS] persistent driver replacement contract + capital gate preserved")
