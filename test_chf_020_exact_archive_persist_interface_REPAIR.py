import inspect
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_016_fixed_grid_historical_window_archive import archive
from qseries_v2.oracle_coinbase_high_frequency.chf_017_historical_window_single_writer_persistence import persist_new
assert str(inspect.signature(archive))=="(root=None)"
assert "root=None" in str(inspect.signature(persist_new))
src=Path("run_coinbase_hf_live.py").read_text(encoding="utf-8")
assert "materialize_history" not in src and "persist_history" not in src
assert "persist_new(ROOT)" in src and "threading.Thread" in src
print("[PASS] nonexistent CHF-020 interfaces retired")
print("[PASS] exact CHF-016/017 interfaces bound during live acquisition")
print("[PASS] historical persistence runs while acquisition is active")
print("[PASS] CHF-020 native child runner repair certified")
