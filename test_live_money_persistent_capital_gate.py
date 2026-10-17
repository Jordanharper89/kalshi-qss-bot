from pathlib import Path
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
