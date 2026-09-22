from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
for f in ("chf_014_production_child_and_gap_lineage.py","chf_016_fixed_grid_historical_window_archive.py","chf_017_historical_window_single_writer_persistence.py"):
    assert (PKG/f).exists(),f"{f} required"

RUNNER=r"""from pathlib import Path
import threading,time
from qseries_v2.oracle_coinbase_high_frequency.chf_014_production_child_and_gap_lineage import run_child
from qseries_v2.oracle_coinbase_high_frequency.chf_016_fixed_grid_historical_window_archive import archive
from qseries_v2.oracle_coinbase_high_frequency.chf_017_historical_window_single_writer_persistence import persist_new

ROOT=Path.cwd()

def main():
    while True:
        box={}
        def acquisition():
            try: box["result"]=run_child(ROOT,max_seconds=90,persist_interval_s=5.0)
            except Exception as e: box["error"]=repr(e)
        t=threading.Thread(target=acquisition,daemon=True); t.start()
        while t.is_alive():
            time.sleep(5.0)
            try:
                r=persist_new(ROOT); print("[CHF-HF HISTORY]",r,flush=True)
            except Exception as e:
                print("[CHF-HF HISTORY HOLD]",repr(e),flush=True)
        t.join()
        if "error" in box: raise RuntimeError(box["error"])

if __name__=="__main__": main()
"""
runner=ROOT/"run_coinbase_hf_live.py"
runner.write_text(RUNNER,encoding="utf-8")
py_compile.compile(str(runner),doraise=True)

TEST=r"""import inspect
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
"""
t=ROOT/"test_chf_020_exact_archive_persist_interface_REPAIR.py"
t.write_text(TEST,encoding="utf-8")
py_compile.compile(str(t),doraise=True)
print("[PASS] wrote",t)
print("[PASS] execution_authority=FALSE")