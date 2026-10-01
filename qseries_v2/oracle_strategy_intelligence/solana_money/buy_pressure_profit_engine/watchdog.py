from __future__ import annotations
import subprocess,sys,threading,time
from pathlib import Path
PRODUCER="qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_profit_engine.producer"
def run_deadline(cmd,timeout,cwd=None):
    t=time.monotonic()
    try:
        p=subprocess.run(cmd,cwd=str(cwd) if cwd else None,capture_output=True,text=True,timeout=timeout)
        return {"timeout":False,"rc":p.returncode,"elapsed":time.monotonic()-t}
    except subprocess.TimeoutExpired:
        return {"timeout":True,"rc":None,"elapsed":time.monotonic()-t}
class Watchdog:
    def __init__(self,root):
        self.root=Path(root).resolve();self.deadlines={"PUMP_FUN":65.0,"PUMP_SWAP":9.0}
        self.state={k:{"runs":0,"ok":0,"timeouts":0,"errors":0,"running":False} for k in self.deadlines}
        self.lock=threading.Lock();self.stop=threading.Event();self.threads=[]
    def _loop(self,lane):
        while not self.stop.is_set():
            with self.lock:self.state[lane]["runs"]+=1;self.state[lane]["running"]=True
            r=run_deadline([sys.executable,"-u","-m",PRODUCER,lane,str(self.root)],self.deadlines[lane],self.root)
            with self.lock:
                s=self.state[lane];s["running"]=False;s["last_elapsed"]=round(r["elapsed"],3)
                if r["timeout"]:s["timeouts"]+=1
                elif r["rc"]==0:s["ok"]+=1
                else:s["errors"]+=1
            self.stop.wait(.1)
    def start(self):
        for lane in self.deadlines:
            t=threading.Thread(target=self._loop,args=(lane,),daemon=True);self.threads.append(t);t.start()
    def snapshot(self):
        with self.lock:return {k:dict(v) for k,v in self.state.items()}
    def close(self):
        self.stop.set()
