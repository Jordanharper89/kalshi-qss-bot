from __future__ import annotations
import threading,time
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

TARGET_WARM=40
REFRESH_SECONDS=20.0

def configure(target=TARGET_WARM):
    target=max(4,int(target))
    engine.MAX_TOKENS=max(int(getattr(engine,"MAX_TOKENS",0)),target)
    engine.DISCOVERY_BUDGET=max(int(getattr(engine,"DISCOVERY_BUDGET",0)),max(96,target*3))
    engine.CROSSLIST_TTL=min(float(getattr(engine,"CROSSLIST_TTL",20.0)),10.0)
    return target

def snapshot(root):
    configure()
    cache=getattr(engine,"_cross_cache",None)
    if isinstance(cache,dict):
        cache["at"]=0.0
    rows=list(engine.candidate_universe(Path(root)) or [])
    return [{
        "token":str(x.get("token") or ""),
        "pump_pool":str(x.get("pump_pool") or ""),
        "source":str(x.get("source") or "UNKNOWN"),
        "age":x.get("age"),
        "meteora_pool":str(x.get("meteora_pool") or ""),
    } for x in rows if x.get("token")]

class ReplenishmentWorker:
    def __init__(self,root,interval=REFRESH_SECONDS):
        self.root=Path(root);self.interval=max(5.0,float(interval))
        self.lock=threading.Lock();self.rows=[];self.generation=0
        self.stop=False;self.thread=None;self.last_error=None
    def refresh(self):
        rows=snapshot(self.root)
        with self.lock:
            old={x["token"] for x in self.rows}
            new={x["token"] for x in rows}
            self.rows=rows;self.generation+=1;self.last_error=None
            g=self.generation
        print("[MRIYA_REPLENISH] generation=%d candidates=%d new=%d mriya=%d"%(
            g,len(rows),len(new-old),sum(1 for x in rows if x["source"]=="MRIYA_HOT")),flush=True)
        return rows
    def latest(self):
        with self.lock:return self.generation,[dict(x) for x in self.rows]
    def _loop(self):
        while not self.stop:
            try:self.refresh()
            except Exception as exc:
                with self.lock:self.last_error="%s:%s"%(type(exc).__name__,exc)
                print("[MRIYA_REPLENISH_WARN] %s"%self.last_error,flush=True)
            for _ in range(int(self.interval*10)):
                if self.stop:return
                time.sleep(.1)
    def start(self):
        if self.thread and self.thread.is_alive():return self
        self.thread=threading.Thread(target=self._loop,name="mriya-replenishment",daemon=True)
        self.thread.start();return self
    def close(self):
        self.stop=True
        if self.thread:self.thread.join(timeout=2)
