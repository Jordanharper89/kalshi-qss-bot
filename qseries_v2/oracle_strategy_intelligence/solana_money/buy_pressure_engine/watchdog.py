from __future__ import annotations
import subprocess,sys,threading,time
from pathlib import Path

PRODUCER_MODULE="qseries_v2.oracle_strategy_intelligence.solana_money.buy_pressure_engine.producer"

def run_with_deadline(cmd,timeout,cwd=None):
    t=time.monotonic()
    try:
        p=subprocess.run(cmd,cwd=str(cwd) if cwd else None,capture_output=True,text=True,
                         timeout=float(timeout))
        return {"timed_out":False,"rc":p.returncode,"elapsed":time.monotonic()-t,
                "stdout":(p.stdout or "")[-2000:],"stderr":(p.stderr or "")[-2000:]}
    except subprocess.TimeoutExpired as e:
        return {"timed_out":True,"rc":None,"elapsed":time.monotonic()-t,
                "stdout":str(e.stdout or "")[-2000:],"stderr":str(e.stderr or "")[-2000:]}

class ProducerWatchdog:
    def __init__(self,root:Path,pumpfun_deadline=12.0,pumpswap_deadline=7.0):
        self.root=Path(root).resolve()
        self.deadlines={"PUMP_FUN":float(pumpfun_deadline),"PUMP_SWAP":float(pumpswap_deadline)}
        self.lock=threading.Lock();self.stop_event=threading.Event();self.threads=[]
        self.state={k:{"heartbeat":0,"completed":0,"timeouts":0,"errors":0,"running":False,
                       "last_elapsed":None,"last_rc":None} for k in self.deadlines}

    def _lane(self,lane):
        while not self.stop_event.is_set():
            with self.lock:
                s=self.state[lane];s["heartbeat"]+=1;s["running"]=True
            cmd=[sys.executable,"-u","-m",PRODUCER_MODULE,lane,str(self.root)]
            r=run_with_deadline(cmd,self.deadlines[lane],self.root)
            with self.lock:
                s=self.state[lane];s["running"]=False;s["last_elapsed"]=round(r["elapsed"],3);s["last_rc"]=r["rc"]
                if r["timed_out"]: s["timeouts"]+=1
                elif r["rc"]==0: s["completed"]+=1
                else: s["errors"]+=1
            self.stop_event.wait(.10)

    def start(self):
        if self.threads:return
        for lane in self.deadlines:
            t=threading.Thread(target=self._lane,args=(lane,),name="QSB024-"+lane,daemon=True)
            self.threads.append(t);t.start()

    def snapshot(self):
        with self.lock:return {k:dict(v) for k,v in self.state.items()}

    def close(self):
        self.stop_event.set()
        for t in self.threads:t.join(timeout=.5)
