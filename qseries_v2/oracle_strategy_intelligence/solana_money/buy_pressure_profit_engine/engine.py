from __future__ import annotations
import math,os,time,uuid
from collections import Counter,defaultdict,deque
from pathlib import Path
from .failure_memory import FailureMemory,FORBIDDEN_ASSETS
from .learning import f,learn
from .persistence import read_json,write_json

PAPER_ONLY=True
EXECUTION_AUTHORITY=False

class ProfitEngine:
    def __init__(self,root:Path,clock=time.time):
        self.root=Path(root).resolve();self.clock=clock
        self.state=self.root/"runtime_state/qseries/qsb026_buy_pressure_profit_engine";self.state.mkdir(parents=True,exist_ok=True)
        self.pos_path=self.state/"positions.json";self.ledger_path=self.state/"ledger.json";self.status_path=self.state/"status.json"
        self.learn_path=self.state/"learning.json";self.fail_path=self.state/"failure_memory.json"
        self.positions=self._load(self.pos_path,{"positions":[]});self.ledger=self._load(self.ledger_path,{"trades":[]})
        self.failure=FailureMemory(self.fail_path,clock=clock)
        self.hist=defaultdict(lambda:deque(maxlen=2000));self.last_mark={};self.last_mark_t={};self.last_win_entry={}
        self.max_open=int(os.getenv("QSB026_MAX_OPEN","12"));self.notional=float(os.getenv("QSB026_NOTIONAL_USDC","5"))
        self.friction=float(os.getenv("QSB026_ROUNDTRIP_FRICTION","0.03"))
        self.stop=float(os.getenv("QSB026_STOP_LOSS","0.055"));self.take=float(os.getenv("QSB026_TAKE_PROFIT","0.12"))
        self.max_hold=90.0;self.event_max_age=float(os.getenv("QSB026_EVENT_MAX_AGE_SECONDS","15"))
        self.reentry_after_win=float(os.getenv("QSB026_REENTRY_AFTER_WIN_SECONDS","20"))
        self.base_quality=float(os.getenv("QSB026_BASE_QUALITY","0.72"))
        self.rejects=Counter();self.events_processed=0;self.batches=0;self.persistence_modes={};self.persist_interval=float(os.getenv("QSB026_PERSIST_INTERVAL_SECONDS","1.0"));self.last_persist_mono=0.0;self.persistence_generations=0
    def _load(self,p,d):
        return read_json(p,d)
    def open(self):return [p for p in self.positions["positions"] if p.get("status")=="OPEN"]

    def _amount(self,rows,side):
        vals=[f(x.get("quote")) for x in rows if x["side"]==side and f(x.get("quote"))>0]
        return sum(vals) if vals else float(sum(x["side"]==side for x in rows))

    def _signal(self,key,now):
        xs=list(self.hist[key])
        if len(xs)<8:return None,"TOO_FEW_EVENTS"
        last=xs[-1]
        if now-last["t"]>self.event_max_age:return None,"STALE_SIGNAL"
        w2=[x for x in xs if x["t"]>=last["t"]-2]
        w5=[x for x in xs if x["t"]>=last["t"]-5]
        prev=[x for x in xs if last["t"]-12<=x["t"]<last["t"]-2]
        if len(w5)<8:return None,"TOO_FEW_5S_EVENTS"
        buys2=[x for x in w2 if x["side"]=="BUY"];buys5=[x for x in w5 if x["side"]=="BUY"]
        if len(buys2)<3:return None,"TOO_FEW_2S_BUYS"
        if len(buys5)<5:return None,"TOO_FEW_5S_BUYS"
        b2,s2=self._amount(w2,"BUY"),self._amount(w2,"SELL")
        b5,s5=self._amount(w5,"BUY"),self._amount(w5,"SELL")
        bp=self._amount(prev,"BUY")
        share2=b2/(b2+s2) if b2+s2 else .5;share5=b5/(b5+s5) if b5+s5 else .5
        rate2=b2/2;rateprev=bp/10 if bp>0 else 0
        accel=rate2/(rateprev+1e-9) if rateprev>0 else (2.0 if rate2>0 else 0.0);accel=min(5.0,accel)
        traders=[x["trader"] for x in buys5 if x.get("trader")]
        identity_coverage=len(traders)/len(buys5) if buys5 else 0
        unique=len(set(traders)) if identity_coverage>=.5 else len(buys5)
        by_wallet=Counter()
        for x in buys5:
            if x.get("trader"):by_wallet[x["trader"]]+=x["quote"] if x["quote"]>0 else 1.0
        total=sum(by_wallet.values());largest=max(by_wallet.values())/total if total>0 else 0.0
        p0=f(w5[0]["price"]);p1=f(last["price"]);momentum=p1/p0-1 if p0>0 else 0
        peak=max(f(x["price"]) for x in w2);drawdown=p1/peak-1 if peak>0 else 0
        if last["side"]!="BUY":return None,"LAST_TRADE_NOT_BUY"
        if share2<.70:return None,"BUY_SHARE_2S"
        if share5<.64:return None,"BUY_SHARE_5S"
        if accel<1.15:return None,"PRESSURE_NOT_ACCELERATING"
        if unique<4:return None,"BUYER_BREADTH"
        if identity_coverage>=.5 and largest>.45:return None,"BUYER_CONCENTRATION"
        if momentum<.015:return None,"NO_PRICE_CONFIRMATION"
        if momentum>.25:return None,"LATE_CHASE"
        if drawdown<-.03:return None,"ROLLING_OVER"
        blocked,why=self.failure.blocked(last["token"],last["market"])
        if blocked:return None,why
        quality=(.24*min(1,(share2-.50)/.35)+.18*min(1,(share5-.50)/.30)+
                 .20*min(1,(accel-1)/2)+.14*min(1,(unique-1)/8)+
                 .14*min(1,momentum/.12)+.10*(1-min(1,largest/.45) if identity_coverage>=.5 else .5))
        return {"market":last["market"],"token":last["token"],"family":last["family"],"price":p1,
                "signal_unix":last["t"],"quality_score":quality,"buy_share_2s":share2,"buy_share_5s":share5,
                "pressure_accel":accel,"unique_buyers_5s":unique,"buyer_identity_coverage":identity_coverage,
                "largest_buyer_share":largest,"momentum_5s":momentum,"birth_age_seconds":f(last.get("birth_age_seconds"),-1),
                "early_buyers":sorted(set(traders))[:30]},"READY"

    def _enter(self,s):
        half=self.friction/2;ref=f(s["price"]);entry=ref*(1+half)
        p={"position_id":"QSB025-"+uuid.uuid4().hex[:16],"status":"OPEN","mode":"PAPER",
           "market":s["market"],"token":s["token"],"family":s["family"],"opened_unix":self.clock(),
           "reference_entry_price":ref,"entry_price":entry,"qty":self.notional/entry,"notional_usdc":self.notional,
           "high_water_price":entry,"low_water_price":entry,"last_mark_price":ref,"last_mark_unix":self.clock(),
           "signal":dict(s),"evidence_valid":True,"real_money_moved":False}
        self.positions["positions"].append(p);return p

    def _close(self,p,mark,reason,evidence_valid=True):
        ref=f(mark,p.get("last_mark_price") or p["reference_entry_price"]);half=self.friction/2
        exit_px=ref*(1-half);net=p["qty"]*exit_px-p["notional_usdc"];entry=f(p["entry_price"])
        p.update(status="CLOSED",closed_unix=self.clock(),reference_exit_price=ref,exit_price=exit_px,
                 exit_reason=reason,net_pnl_usdc=net,net_return=net/p["notional_usdc"],
                 mfe=f(p["high_water_price"])/entry-1,mae=f(p["low_water_price"])/entry-1,
                 evidence_valid=bool(evidence_valid))
        self.ledger["trades"].append(dict(p))
        if evidence_valid and net<=0:self.failure.record_loss(p["token"],p["market"],net,reason,p.get("signal"))
        if evidence_valid and net>0:self.last_win_entry[p["token"]]=self.clock()
        return dict(p)

    def _manage(self,latest,now):
        closed=[]
        for p in list(self.open()):
            key=(p["market"],p["token"]);mark=latest.get(key)
            if mark is not None:
                p["last_mark_price"]=mark["price"];p["last_mark_unix"]=mark["t"]
                p["high_water_price"]=max(f(p["high_water_price"],p["entry_price"]),mark["price"])
                p["low_water_price"]=min(f(p["low_water_price"],p["entry_price"]),mark["price"])
            age=now-f(p["opened_unix"]);px=f(p.get("last_mark_price"),p["reference_entry_price"]);entry=f(p["entry_price"])
            fresh=now-f(p.get("last_mark_unix"),0)<=10
            if age>=self.max_hold:
                if fresh:closed.append(self._close(p,px,"MAX_HOLD",True))
                else:closed.append(self._close(p,px,"DATA_GAP_ABORT",False))
                continue
            if not fresh:continue
            ret=px/entry-1;trail=px/f(p["high_water_price"],entry)-1
            if ret<=-self.stop:closed.append(self._close(p,px,"STOP_LOSS",True));continue
            if ret>=self.take:closed.append(self._close(p,px,"TAKE_PROFIT",True));continue
            # Trailing stop cannot fire until the trade has a genuine gross-profit cushion.
            if f(p["high_water_price"])>=entry*1.10 and trail<=-.05:
                closed.append(self._close(p,px,"TRAILING_STOP",True));continue
            if age>=3:
                sig,why=self._signal(key,now)
                if sig and sig["buy_share_2s"]<.42 and sig["momentum_5s"]<0:
                    closed.append(self._close(p,px,"PRESSURE_COLLAPSE",True))
        return closed

    def on_batch(self,events):
        now=self.clock();self.batches+=1;latest={};keys=set()
        # Phase 1: consume the entire artifact batch into evidence. NO ENTRY occurs while
        # backfilled rows are being replayed, preventing 0.00s fake round-trips.
        for e in events:
            if e["token"] in FORBIDDEN_ASSETS:
                self.rejects["FORBIDDEN_QUOTE_ASSET"]+=1;continue
            self.hist[(e["market"],e["token"])].append(dict(e));self.events_processed+=1
            key=(e["market"],e["token"]);keys.add(key)
            if key not in latest or e["t"]>=latest[key]["t"]:latest[key]=dict(e)
            self.last_mark[key]=e["price"];self.last_mark_t[key]=e["t"]
        closed=self._manage(latest,now)

        L=learn(self.ledger["trades"],self.base_quality)
        entered=[];open_tokens={p["token"] for p in self.open()}
        for key in keys:
            sig,why=self._signal(key,now)
            if not sig:
                self.rejects[why]+=1;continue
            if sig["token"] in open_tokens:
                self.rejects["ALREADY_OPEN"]+=1;continue
            if now-f(self.last_win_entry.get(sig["token"],0))<self.reentry_after_win:
                self.rejects["WIN_REENTRY_COOLDOWN"]+=1;continue
            if sig["quality_score"]<f(L["quality_floor"],self.base_quality):
                self.rejects["QUALITY_FLOOR"]+=1;continue
            if len(self.open())>=self.max_open:
                self.rejects["POSITION_CAP"]+=1;break
            entered.append(self._enter(sig));open_tokens.add(sig["token"])
        self.persist(force=bool(entered or closed))
        return entered,closed

    def heartbeat(self):
        now=self.clock();closed=self._manage({},now);self.persist(force=bool(closed));return closed

    def stats(self):
        valid=[x for x in self.ledger["trades"] if x.get("evidence_valid",True)]
        aborts=[x for x in self.ledger["trades"] if not x.get("evidence_valid",True)]
        wins=sum(f(x.get("net_pnl_usdc"))>0 for x in valid);losses=len(valid)-wins
        net=sum(f(x.get("net_pnl_usdc")) for x in valid);L=learn(valid,self.base_quality)
        return {"events":self.events_processed,"batches":self.batches,"open":len(self.open()),
                "closed_valid":len(valid),"data_gap_aborts":len(aborts),"wins":wins,"losses":losses,
                "win_rate":wins/len(valid) if valid else None,"net_pnl_usdc":net,
                "milestone":wins>=10 and net>0,"learning":L,"rejects":dict(self.rejects)}
    def persist(self,force=False):
        mono=time.monotonic()
        if not force and self.last_persist_mono and mono-self.last_persist_mono<self.persist_interval:return False
        s=self.stats();self.persistence_modes={}
        self.persistence_modes["positions"]=write_json(self.pos_path,self.positions)
        self.persistence_modes["ledger"]=write_json(self.ledger_path,self.ledger)
        self.persistence_modes["learning"]=write_json(self.learn_path,s["learning"])
        self.persistence_modes["status"]=write_json(self.status_path,s)
        self.last_persist_mono=mono;self.persistence_generations+=1;return True
