from __future__ import annotations
from .persistence import read_json,write_json

HORIZONS=(1,3,5,10,20,30,60,90)

class OutcomeBook:
    def __init__(self,path):
        self.path=path;self.data=read_json(path,{"active":{},"finalized":[]})
    def start(self,c):
        cid=c["candidate_id"]
        if cid in self.data["active"]:return
        self.data["active"][cid]={"candidate":dict(c),"max_price":c["signal_price"],"min_price":c["signal_price"],
                                  "last_price":c["signal_price"],"horizons":{}}
    def update_event(self,e):
        key=(e["market"],e["token"]);done=[]
        for cid,o in list(self.data["active"].items()):
            c=o["candidate"]
            if (c["market"],c["token"])!=key or e["t"]<=c["signal_event_t"]:continue
            px=float(e["price"]);o["last_price"]=px;o["max_price"]=max(o["max_price"],px);o["min_price"]=min(o["min_price"],px)
            elapsed=e["t"]-c["signal_event_t"]
            for h in HORIZONS:
                k=str(h)
                if elapsed>=h and k not in o["horizons"]:
                    base=c["signal_price"]
                    o["horizons"][k]={"return":px/base-1,"mfe":o["max_price"]/base-1,"mae":o["min_price"]/base-1}
            if elapsed>=90:done.append(cid)
        for cid in done:self._finish(cid)
    def heartbeat(self,now,last_marks):
        done=[]
        for cid,o in self.data["active"].items():
            c=o["candidate"];elapsed=now-c["signal_event_t"]
            if elapsed<90:continue
            px=last_marks.get((c["market"],c["token"]),o["last_price"]);base=c["signal_price"]
            for h in HORIZONS:
                k=str(h)
                if k not in o["horizons"] and elapsed>=h:
                    o["horizons"][k]={"return":px/base-1,"mfe":o["max_price"]/base-1,"mae":o["min_price"]/base-1}
            done.append(cid)
        for cid in done:self._finish(cid)
    def _finish(self,cid):
        o=self.data["active"].pop(cid);o["finalized"]=True;self.data["finalized"].append(o)
        self.data["finalized"]=self.data["finalized"][-10000:]
    def pattern_stats(self,pattern):
        xs=[]
        for o in self.data["finalized"]:
            c=o["candidate"];h=o["horizons"].get("10")
            if c.get("pattern")==pattern and h:xs.append(h)
        if not xs:return {"n":0,"success_rate":None,"avg_return":None}
        # A 10s continuation is useful only if it clears 3% modeled friction plus margin.
        wins=[x for x in xs if x["mfe"]>=.05 and x["return"]>=.03]
        return {"n":len(xs),"success_rate":len(wins)/len(xs),"avg_return":sum(x["return"] for x in xs)/len(xs)}
    def save(self):return write_json(self.path,self.data)
