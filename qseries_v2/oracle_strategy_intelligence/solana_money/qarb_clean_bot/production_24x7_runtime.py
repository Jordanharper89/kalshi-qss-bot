from __future__ import annotations
import argparse,json,os,signal,time,traceback
from pathlib import Path
from datetime import datetime,timezone

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as live

DEFAULT_WINDOW=float(os.getenv("QARB_PRODUCTION_WINDOW_SECONDS","3600"))
RESTART_DELAY=float(os.getenv("QARB_RESTART_DELAY_SECONDS","1.0"))
MAX_RESTART_DELAY=float(os.getenv("QARB_MAX_RESTART_DELAY_SECONDS","30.0"))
STATE_REL=Path("runtime_state/qseries/qarb_clean_bot/production_24x7_status.json")
JOURNAL_REL=Path("runtime_state/qseries/qarb_clean_bot/production_24x7_windows.jsonl")

_STOP=False

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def _stop(*_):
    global _STOP
    _STOP=True

def _write_json_atomic(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,sort_keys=True,indent=2),encoding="utf-8")
    tmp.replace(path)

def _append_jsonl(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n")

def _status(root,**kw):
    p=Path(root)/STATE_REL
    current={
      "service":"QARB-022",
      "execution_authority":False,
      "pid":os.getpid(),
      "updated_at":utc_now(),
    }
    current.update(kw)
    _write_json_atomic(p,current)
    return current

def _run_window(root,window_seconds):
    import asyncio
    return asyncio.run(live.run(Path(root),float(window_seconds)))

def run_forever(root,window_seconds=DEFAULT_WINDOW,max_windows=None,runner=None,sleep_fn=time.sleep):
    root=Path(root)
    runner=runner or _run_window
    signal.signal(signal.SIGINT,_stop)
    if hasattr(signal,"SIGTERM"):
        signal.signal(signal.SIGTERM,_stop)

    restart_delay=RESTART_DELAY
    windows=0
    starts=utc_now()
    _status(root,state="STARTING",started_at=starts,window_seconds=float(window_seconds),windows_completed=0)
    print("[QARB-022C] PRODUCTION 24/7 ARBITRAGE RUNTIME",flush=True)
    print("[RUN] persistent service | Ctrl+C to stop",flush=True)
    print("[HOT] profitable locally-priced route prints immediately as [HOT_SIGNAL]",flush=True)
    print("[GATE] event_to_decision <=750ms",flush=True)
    print("[RECOVERY] reconnect/rebuild after any window failure",flush=True)
    print("[MODE] scanner/handoff only execution_authority=FALSE",flush=True)

    while not _STOP:
        if max_windows is not None and windows>=int(max_windows):
            break
        opened=utc_now()
        _status(root,state="RUNNING",started_at=starts,window_started_at=opened,
                window_seconds=float(window_seconds),windows_completed=windows)
        try:
            result=runner(root,float(window_seconds))
            windows+=1
            row={"opened_at":opened,"closed_at":utc_now(),"ok":True,"result":result}
            _append_jsonl(root/JOURNAL_REL,row)
            best=(result or {}).get("best") if isinstance(result,dict) else None
            print("[WINDOW] n=%d notifications=%s signals=%s best_net_sol=%s rate_limits=%s"%(
                windows,
                (result or {}).get("notifications") if isinstance(result,dict) else None,
                (result or {}).get("signals") if isinstance(result,dict) else None,
                None if not best else best.get("net_sol"),
                (result or {}).get("rate_limited_connections") if isinstance(result,dict) else None,
            ),flush=True)
            _status(root,state="RUNNING",started_at=starts,window_seconds=float(window_seconds),
                    windows_completed=windows,last_result=result,last_window_closed_at=row["closed_at"])
            restart_delay=RESTART_DELAY
        except KeyboardInterrupt:
            break
        except Exception as exc:
            row={"opened_at":opened,"closed_at":utc_now(),"ok":False,
                 "error":f"{type(exc).__name__}: {exc}"}
            _append_jsonl(root/JOURNAL_REL,row)
            _status(root,state="RECOVERING",started_at=starts,window_seconds=float(window_seconds),
                    windows_completed=windows,last_error=row["error"],restart_delay_seconds=restart_delay)
            print("[RECOVER] %s | retry_in=%.2fs"%(row["error"],restart_delay),flush=True)
            sleep_fn(restart_delay)
            restart_delay=min(MAX_RESTART_DELAY,max(RESTART_DELAY,restart_delay*2.0))

    final=_status(root,state="STOPPED",started_at=starts,window_seconds=float(window_seconds),
                  windows_completed=windows,stopped_at=utc_now())
    print("[STOPPED] windows_completed=%d"%windows,flush=True)
    return final

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--window-seconds",type=float,default=DEFAULT_WINDOW)
    ap.add_argument("--max-windows",type=int,default=None,
                    help="test/maintenance only; omit for 24/7")
    a=ap.parse_args(argv)
    return run_forever(Path.cwd(),a.window_seconds,a.max_windows)

if __name__=="__main__":
    main()
