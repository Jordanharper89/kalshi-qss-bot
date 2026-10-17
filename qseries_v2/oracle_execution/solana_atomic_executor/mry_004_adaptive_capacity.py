from __future__ import annotations
class CapacityController:
    def __init__(self,start=20,minimum=4,maximum=40):
        self.target=max(minimum,min(maximum,int(start)))
        self.minimum=int(minimum);self.maximum=int(maximum)
        self.healthy_streak=0
    def observe(self,metrics):
        rate=int(metrics.get("rate_limits") or 0)
        reconnects=int(metrics.get("reconnects") or 0)
        p95=float(metrics.get("p95_event_age_ms") or 0.0)
        pricing=float(metrics.get("p95_pricing_ms") or 0.0)
        overloaded=bool(rate>0 or reconnects>1 or p95>40.0 or pricing>15.0)
        if overloaded:
            self.target=max(self.minimum,self.target-4);self.healthy_streak=0
            return self.target
        self.healthy_streak+=1
        if self.healthy_streak>=3:
            self.target=min(self.maximum,self.target+2);self.healthy_streak=0
        return self.target

def percentile(rows,q):
    vals=sorted(float(x) for x in rows if x is not None)
    if not vals:return 0.0
    i=min(len(vals)-1,max(0,int((len(vals)-1)*float(q))))
    return vals[i]
