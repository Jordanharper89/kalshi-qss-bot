from __future__ import annotations
import json,math,os,time,uuid
from collections import Counter,defaultdict,deque
from pathlib import Path
from .learning import f,model,adjusted_score

PAPER_ONLY=True
EXECUTION_AUTHORITY=False

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    data=json.dumps(obj,indent=2,sort_keys=True,default=str)
    for i in range(5):
        tmp=path.with_name(path.name+f".{os.getpid()}.{i}.tmp")
        try:
            tmp.write_text(data,encoding="utf-8");os.replace(tmp,path);return
        except PermissionError:
            try:tmp.unlink(missing_ok=True)
            except Exception:pass
            time.sleep(.02*(i+1))
    path.write_text(data,encoding="utf-8")

class EventDrivenBuyPressureEngine:
    def __init__(self,root:Path,clock=time.time):
        self.root=Path(root).resolve();self.clock=clock
        self.state=self.root/"runtime_state/qseries/qsb024_pump_buy_pressure";self.state.mkdir(parents=True,exist_ok=True)
        self.pos_path=self.state/"positions.json";self.ledger_path=self.state/"ledger.json"
        self.learning_path=self.state/"learning.json";self.wallet_path=self.state/"wallets.json";self.status_path=self.state/"status.json"
        self.positions=self._load(self.pos_path,{"positions":[]});self.ledger=self._load(self.ledger_path,{"trades":[]})
        self.wallets=self._load(self.wallet_path,{"wallets":{}})
        self.events=defaultdict(lambda:deque(maxlen=1000));self.last_entry={};self.last_mark={};self.last_mark_t={}
        self.max_open=int(os.getenv("QSB024_MAX_OPEN","48"))
        self.friction=float(os.getenv("QSB024_ROUNDTRIP_FRICTION","0.03"))
        self.notional=float(os.getenv("QSB024_NOTIONAL_USDC","5"))
        self.base_gate=float(os.getenv("QSB024_ADMISSION_SCORE","0.56"))
        self.base_stop=float(os.getenv("QSB024_STOP_LOSS","0.07"))
        self.base_take=float(os.getenv("QSB024_TAKE_PROFIT","0.12"))
        self.max_hold=float(os.getenv("QSB024_MAX_HOLD_SECONDS","90"))
        self.reentry=float(os.getenv("QSB024_REENTRY_SECONDS","2"))
        self.evaluations=0;self.events_processed=0

    def _load(self,p,d):
        try:return json.loads(p.read_text(encoding="utf-8"))
        except Exception:return d

    def open(self):return [x for x in self.positions["positions"] if x.get("status")=="OPEN"]

    def _amount(self,rows,side):
        vals=[f(x.get("quote")) for x in rows if x.get("side")==side and f(x.get("quote"))>0]
        return sum(vals) if vals else float(sum(x.get("side")==side for x in rows))

    def _wallet_quality(self,buyers):
        q=[]
        for w in buyers:
            d=self.wallets["wallets"].get(w)
            if not d or int(d.get("trades") or 0)<2:continue
            n=int(d["trades"]);wins=int(d["wins"]);net=f(d.get("net"))
            x=(wins+1)/(n+2)
            if net<0:x-=.08
            q.append(max(0,min(1,x)))
        return sum(q)/len(q) if q else .5

    def signal(self,key):
        xs=list(self.events[key])
        if len(xs)<3:return None
        last=xs[-1];t=last["t"]
        w2=[x for x in xs if x["t"]>=t-2]
        w5=[x for x in xs if x["t"]>=t-5]
        prev=[x for x in xs if t-10<=x["t"]<t-2]
        if len(w5)<3:return None
        b2,s2=self._amount(w2,"BUY"),self._amount(w2,"SELL")
        b5,s5=self._amount(w5,"BUY"),self._amount(w5,"SELL")
        bp=self._amount(prev,"BUY")
        share2=b2/(b2+s2) if b2+s2 else .5
        share5=b5/(b5+s5) if b5+s5 else .5
        rate2=b2/2
        rateprev=bp/8 if bp>0 else 0
        accel=rate2/(rateprev+1e-9) if rateprev>0 else (2.0 if rate2>0 else 0)
        accel=min(5.0,accel)
        buyers=[x.get("trader") for x in w5 if x.get("side")=="BUY" and x.get("trader")]
        unique=len(set(buyers)) if buyers else sum(x.get("side")=="BUY" for x in w5)
        priced=[x for x in w5 if f(x.get("price"))>0]
        momentum=(f(priced[-1]["price"])/f(priced[0]["price"])-1) if len(priced)>=2 else 0
        birth=f(last.get("birth_age_seconds"),-1)
        wallet_q=self._wallet_quality(set(buyers))
        if share2<.58 or share5<.56 or unique<2 or momentum<-.012:return None
        if not (accel>=.90 or share2>=.72):return None
        score=(.28*max(0,min(1,(share2-.50)/.35))+
               .22*max(0,min(1,(share5-.50)/.30))+
               .20*max(0,min(1,(accel-.9)/2.1))+
               .12*max(0,min(1,(unique-1)/7))+
               .10*max(0,min(1,max(0,momentum)/.10))+
               .08*max(0,min(1,(wallet_q-.35)/.45)))
        return {"market":key[0],"token":key[1],"family":last["family"],"signal_unix":t,"price":last["price"],
                "score":score,"buy_share_2s":share2,"buy_share_5s":share5,"pressure_accel":accel,
                "unique_buyers_5s":unique,"momentum_5s":momentum,"wallet_quality":wallet_q,
                "birth_age_seconds":birth,"early_buyers":sorted(set(buyers))[:30]}

    def _enter(self,s,m):
        half=self.friction/2;ref=f(s["price"]);entry=ref*(1+half);now=self.clock()
        p={"position_id":"QSB024-"+uuid.uuid4().hex[:16],"status":"OPEN","mode":"PAPER",
           "market":s["market"],"token":s["token"],"family":s["family"],"opened_unix":now,
           "reference_entry_price":ref,"entry_price":entry,"qty":self.notional/entry,"notional_usdc":self.notional,
           "high_water_price":entry,"low_water_price":entry,"last_mark_price":ref,"last_mark_unix":now,
           "signal":dict(s),"real_money_moved":False}
        self.positions["positions"].append(p);self.last_entry[s["token"]]=now;return p

    def _learn_wallets(self,t):
        win=f(t.get("net_pnl_usdc"))>0
        for w in (t.get("signal") or {}).get("early_buyers") or []:
            d=self.wallets["wallets"].setdefault(w,{"trades":0,"wins":0,"losses":0,"net":0.0})
            d["trades"]+=1;d["wins"]+=1 if win else 0;d["losses"]+=0 if win else 1;d["net"]+=f(t.get("net_pnl_usdc"))

    def _close(self,p,mark,reason,stale=False):
        half=self.friction/2;ref=f(mark,p.get("last_mark_price") or p["reference_entry_price"])
        if stale:ref*=.995
        exit_px=ref*(1-half);net=p["qty"]*exit_px-p["notional_usdc"];entry=f(p["entry_price"])
        p.update(status="CLOSED",closed_unix=self.clock(),reference_exit_price=ref,exit_price=exit_px,
                 exit_reason=reason,net_pnl_usdc=net,net_return=net/p["notional_usdc"],
                 mfe=f(p["high_water_price"])/entry-1,mae=f(p["low_water_price"])/entry-1)
        self.ledger["trades"].append(dict(p));self._learn_wallets(p);return dict(p)

    def _manage_key(self,key,mark,pressure=None):
        now=self.clock();closed=[]
        m=model(self.ledger["trades"],self.base_gate,self.base_stop,self.base_take,self.max_hold)
        for p in self.open():
            if (p["market"],p["token"])!=key:continue
            age=now-f(p["opened_unix"]);entry=f(p["entry_price"])
            p["last_mark_price"]=mark;p["last_mark_unix"]=now
            p["high_water_price"]=max(f(p["high_water_price"],entry),mark);p["low_water_price"]=min(f(p["low_water_price"],entry),mark)
            ret=mark/entry-1;trail=mark/f(p["high_water_price"],entry)-1;reason=None
            if ret<=-f(m["stop_loss"],self.base_stop):reason="STOP_LOSS"
            elif ret>=f(m["take_profit"],self.base_take):reason="TAKE_PROFIT"
            elif f(p["high_water_price"])>=entry*1.04 and trail<=-.045:reason="TRAILING_STOP"
            elif age>=1 and pressure is not None and f(pressure.get("buy_share_2s"),.5)<.40:reason="PRESSURE_COLLAPSE"
            elif age>=f(m["max_hold_seconds"],self.max_hold):reason="MAX_HOLD"
            if reason:closed.append(self._close(p,mark,reason))
        return closed

    def on_event(self,e):
        self.events_processed+=1;self.evaluations+=1
        key=(e["market"],e["token"]);self.events[key].append(dict(e))
        self.last_mark[key]=f(e["price"]);self.last_mark_t[key]=f(e["t"])
        pre=self.signal(key)
        closed=self._manage_key(key,f(e["price"]),pre)
        m=model(self.ledger["trades"],self.base_gate,self.base_stop,self.base_take,self.max_hold)
        s=self.signal(key);entered=[]
        if s:
            s["adaptive_score"]=adjusted_score(s,m)
            open_tokens={p["token"] for p in self.open()}
            if (len(self.open())<self.max_open and s["token"] not in open_tokens and
                self.clock()-f(self.last_entry.get(s["token"],0))>=self.reentry and
                s["adaptive_score"]>=f(m["admission_score"],self.base_gate)):
                entered.append(self._enter(s,m))
        return entered,closed

    def heartbeat(self):
        now=self.clock();closed=[]
        m=model(self.ledger["trades"],self.base_gate,self.base_stop,self.base_take,self.max_hold)
        max_hold=f(m["max_hold_seconds"],self.max_hold)
        for p in list(self.open()):
            age=now-f(p["opened_unix"])
            if age<max_hold:continue
            key=(p["market"],p["token"]);mark=f(self.last_mark.get(key),p.get("last_mark_price") or p["reference_entry_price"])
            fresh=now-f(self.last_mark_t.get(key),0)<=5
            closed.append(self._close(p,mark,"MAX_HOLD" if fresh else "STALE_MAX_HOLD",stale=not fresh))
        return closed

    def status(self):
        wins=sum(f(x.get("net_pnl_usdc"))>0 for x in self.ledger["trades"])
        losses=len(self.ledger["trades"])-wins;net=sum(f(x.get("net_pnl_usdc")) for x in self.ledger["trades"])
        m=model(self.ledger["trades"],self.base_gate,self.base_stop,self.base_take,self.max_hold)
        s={"revision":"QSB_024_PUMP_BUY_PRESSURE_EVENT_DRIVEN_MONEY_ENGINE_V1","paper_only":True,
           "execution_authority":False,"events_processed":self.events_processed,"evaluations":self.evaluations,
           "markets":len(self.events),"open":len(self.open()),"closed":len(self.ledger["trades"]),
           "wins":wins,"losses":losses,"win_rate":wins/len(self.ledger["trades"]) if self.ledger["trades"] else None,
           "net_pnl_usdc":net,"milestone":wins>=10 and net>0,"learning":m}
        save(self.pos_path,self.positions);save(self.ledger_path,self.ledger);save(self.wallet_path,self.wallets)
        save(self.learning_path,m);save(self.status_path,s);return s
