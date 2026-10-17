from __future__ import annotations
import time
from . import mry_001_continuous_replenishment as m1
from . import mry_002_warm_inventory as m2
from . import mry_003_hot_rotation as m3
from . import mry_004_adaptive_capacity as m4
from . import mry_010_live_promotion as m10

ROTATE_SECONDS=60.0
ACCOUNT_BUDGET=480

async def serve_rotating(rt,root,state,seconds,lane):
    worker=m1.ReplenishmentWorker(root).start()
    ctl=m4.CapacityController(start=20,minimum=4,maximum=40)
    cursor=0;started=time.monotonic();last_positive=int(getattr(lane,"positive",0))
    segment=0
    try:
        while time.monotonic()-started<float(seconds):
            segment+=1
            generation,hints=worker.latest()
            m10.admit_batch(rt,root,state,hints)
            inv=m2.inventory(state,rt.READY_TOKENS,hints)
            selected=m3.select_hot(inv,ctl.target,ACCOUNT_BUDGET,cursor)
            if not selected:raise RuntimeError("MRIYA_NO_HOT_READY_PAIRS")
            view=m3.hot_view(state,selected)
            queued=[x for x in hints if x.get("token") not in {r["token"] for r in inv}]
            print("[MRIYA_HOT_SET] segment=%d target=%d active=%d warm=%d accounts=%d generation=%d queued_unhydrated=%d"%(
                segment,ctl.target,len(selected),len(inv),len(view["addresses"]),generation,len(queued)),flush=True)
            age0=len(getattr(lane,"event_start_ms",[]) or [])
            scan0=len(getattr(lane,"scan_ms",[]) or [])
            left=float(seconds)-(time.monotonic()-started)
            result=await rt.serve_canonical(view,min(ROTATE_SECONDS,max(.1,left)),lane)
            positives=int(getattr(lane,"positive",0))
            idle=(positives==last_positive)
            last_positive=positives
            ages=list(getattr(lane,"event_start_ms",[]) or [])[age0:]
            scans=list(getattr(lane,"scan_ms",[]) or [])[scan0:]
            metrics={
                "rate_limits":int(result.get("rate_limit_disconnects") or 0),
                "reconnects":int(result.get("reconnects") or 0),
                "p95_event_age_ms":m4.percentile(ages,.95),
                "p95_pricing_ms":m4.percentile(scans,.95),
            }
            old=ctl.target;ctl.observe(metrics)
            if idle:cursor=(cursor+max(1,len(selected)//2))%max(1,len(inv))
            print("[MRIYA_ROTATE] idle=%s old_target=%d new_target=%d cursor=%d p95_age_ms=%.3f p95_pricing_ms=%.3f rate_limits=%d reconnects=%d"%(
                idle,old,ctl.target,cursor,metrics["p95_event_age_ms"],metrics["p95_pricing_ms"],metrics["rate_limits"],metrics["reconnects"]),flush=True)
    finally:
        worker.close()
    return {"segments":segment,"positive":int(getattr(lane,"positive",0))}
