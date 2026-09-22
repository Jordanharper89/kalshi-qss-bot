from pathlib import Path
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
