import json,time,threading
from datetime import datetime,timezone
from pathlib import Path
from .chf_002_live_event_worker import CoinbaseHFWorker
from .chf_006_continuous_multihorizon_worker import ContinuousWindowWorker
from .chf_013_strict_window_single_writer_persistence import persist_strict_windows

REVISION="CHF-014"

def _now(): return datetime.now(timezone.utc).isoformat()

def run_child(root=None,max_seconds=None,persist_interval_s=5.0):
    root=Path(root or Path.cwd()).resolve()
    d=root/"runtime"/"coinbase_hf"; d.mkdir(parents=True,exist_ok=True)
    lineage=d/"gap_lineage.jsonl"
    ws=CoinbaseHFWorker(root)
    normalizer=ContinuousWindowWorker(root)
    stop=threading.Event()
    errors=[]
    def acquire():
        try: ws.run(max_seconds=max_seconds)
        except Exception as e: errors.append(repr(e)); stop.set()
    t=threading.Thread(target=acquire,name="CHF-Coinbase-WebSocket",daemon=True)
    t.start()
    started=time.monotonic(); cycles=0; last_raw_size=0; last_growth=time.monotonic()
    while not stop.is_set():
        normalizer.cycle()
        raw=normalizer.raw
        size=raw.stat().st_size if raw.exists() else 0
        if size>last_raw_size:
            last_growth=time.monotonic(); last_raw_size=size
        elif time.monotonic()-last_growth>10:
            rec={"detected_at":_now(),"status":"LIVE_GAP_DETECTED","gap_seconds":round(time.monotonic()-last_growth,3),"backfill_status":"UNRECOVERABLE_UNLESS_EXACT_SOURCE_BACKFILL_EXISTS","execution_authority":False}
            with lineage.open("a",encoding="utf-8") as f:f.write(json.dumps(rec,separators=(",",":"))+"\n")
            last_growth=time.monotonic()
        try:
            r=persist_strict_windows(root)
            if r["submitted"] or r["skipped_existing"]:
                print("[CHF-014 PERSIST]",r,flush=True)
        except Exception as e:
            print("[CHF-014 HOLD]",repr(e),flush=True)
        cycles+=1
        if max_seconds is not None and time.monotonic()-started>=max_seconds: break
        time.sleep(persist_interval_s)
    t.join(timeout=3)
    if errors: raise RuntimeError(errors[0])
    return {"cycles":cycles,"raw_size":last_raw_size,"gap_lineage":str(lineage),"execution_authority":False}
