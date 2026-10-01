from __future__ import annotations
import builtins,json,re,threading,time
from pathlib import Path
from qseries_v2.oracle_execution import oracle_034_positive_only_paper_attack_lane as q34

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
REPORT=Path("runtime_state/oracle/oracle_live_execution/oracle_035_positive_opportunity_lifecycle.json")

RX=re.compile(
    r"^\[ORACLE028_EXACT_CURRENT\] token=(\S+) slot=(\d+) dir=(\S+) "
    r"size=([0-9.]+) bps=([+-]?[0-9.]+) net=([+-]?\d+) "
    r"start_ms=([0-9.]+) materialize_ms=([0-9.]+) scan_ms=([0-9.]+)"
)
_lock=threading.Lock()
_active={}
_closed=[]
_original_print=None

def observe_line(line,now=None):
    m=RX.match(str(line))
    if not m:return
    now=float(time.time() if now is None else now)
    token,slot,direction,size,bps,net,start,mat,scan=m.groups()
    bps=float(bps); net=int(net)
    key=token
    with _lock:
        ep=_active.get(key)
        if net>0:
            if ep is None:
                ep={
                    "token":token,"direction":direction,
                    "first_positive_epoch":now,"last_positive_epoch":now,
                    "first_slot":int(slot),"last_slot":int(slot),
                    "consecutive_positive_updates":0,
                    "peak_bps":bps,"peak_net_lamports":net,
                    "last_size_sol":float(size),
                }
                _active[key]=ep
            ep["last_positive_epoch"]=now
            ep["last_slot"]=int(slot)
            ep["consecutive_positive_updates"]+=1
            ep["peak_bps"]=max(float(ep["peak_bps"]),bps)
            ep["peak_net_lamports"]=max(int(ep["peak_net_lamports"]),net)
            ep["last_size_sol"]=float(size)
            ep["direction"]=direction
        elif ep is not None:
            ep=dict(ep)
            ep["closed_epoch"]=now
            ep["positive_duration_ms"]=max(
                0.0,(float(ep["last_positive_epoch"])-float(ep["first_positive_epoch"]))*1000.0
            )
            _closed.append(ep)
            del _active[key]
            builtins.__dict__["print"](
                "[ORACLE035_LIFECYCLE_CLOSE] token=%s updates=%d peak_bps=%+.2f duration_ms=%.3f"
                %(token[:10],ep["consecutive_positive_updates"],ep["peak_bps"],ep["positive_duration_ms"]),
                flush=True,
            )

def _hook(*args,**kwargs):
    line=" ".join(str(x) for x in args)
    observe_line(line)
    _original_print(*args,**kwargs)

def install_hook():
    global _original_print
    if _original_print is None:
        _original_print=builtins.print
        builtins.print=_hook

def restore_hook():
    global _original_print
    if _original_print is not None:
        builtins.print=_original_print
        _original_print=None

def finalize():
    now=time.time()
    with _lock:
        for token,ep0 in list(_active.items()):
            ep=dict(ep0)
            ep["closed_epoch"]=now
            ep["positive_duration_ms"]=max(
                0.0,(float(ep["last_positive_epoch"])-float(ep["first_positive_epoch"]))*1000.0
            )
            ep["open_at_runtime_end"]=True
            _closed.append(ep)
        _active.clear()
        rows=list(_closed)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({
        "oracle_build":"ORACLE-035",
        "episodes":rows,
        "episode_count":len(rows),
        "execution_authority":False,
        "paper_only":True,
    },indent=2,sort_keys=True),encoding="utf-8")
    return rows

def run(seconds=300.0):
    install_hook()
    try:
        print("[ORACLE-035] POSITIVE OPPORTUNITY LIFECYCLE",flush=True)
        print("[TRACK] consecutive positive updates + lifetime + peak edge",flush=True)
        print("[BROADCAST] disabled",flush=True)
        return q34.run(seconds=seconds)
    finally:
        restore_hook()
        rows=finalize()
        print("[ORACLE035_COMPLETE] episodes=%d report=%s"%(len(rows),REPORT),flush=True)
