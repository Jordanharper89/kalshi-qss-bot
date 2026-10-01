from __future__ import annotations
import math,os,time,uuid
from collections import Counter,defaultdict,deque
from pathlib import Path
from .failure_memory import FailureMemory
from .persistence import read_json,write_json
from .outcomes import OutcomeBook

def f(v,d=0.0):
    try:
        x=float(v);return x if math.isfinite(x) else float(d)
    except Exception:return float(d)

class ForwardConfirmedEngine:
    def __init__(self,root:Path,clock=time.time):
        self.root=Path(root).resolve();self.clock=clock
        self.state=self.root/"runtime_state/qseries/qsb027_forward_confirmed_buy_pressure";self.state.mkdir(parents=True,exist_ok=True)
        self.positions_path=self.state/"positions.json";self.ledger_path=self.state/"ledger.json"
        self.candidates_path=self.state/"candidates.json";self.status_path=self.state/"status.json"
        self.outcome_path=self.state/"candidate_outcomes.json";self.failure_path=self.state/"failure_memory.json"
        self.positions=read_json(self.positions_path,{"positions":[]});self.ledger=read_json(self.ledger_path,{"trades":[]})
        self.candidates=read_json(self.candidates_path,{"active":{},"archive":[]})
        self.failure=FailureMemory(self.failure_path,clock);self.outcomes=OutcomeBook(self.outcome_path)
        self.hist=defaultdict(lambda:deque(maxlen=2500));self.last_marks={};self.last_mark_t={}
        self.rejects=Counter();self.events=0;self.batches=0;self.confirmed=0;self.formed=0
        self.notional=float(os.getenv("QSB027_NOTIONAL_USDC","5"));self.friction=float(os.getenv("QSB027_ROUNDTRIP_FRICTION","0.03"))
        self.max_open=int(os.getenv("QSB027_MAX_OPEN","10"));self.max_hold=90.0
        self.max_signal_arrival=float(os.getenv("QSB027_MAX_SIGNAL_ARRIVAL_SECONDS","2.0"))
        self.max_confirm_arrival=float(os.getenv("QSB027_MAX_CONFIRM_ARRIVAL_SECONDS","2.0"))
        self.max_candidate_age=float(os.getenv("QSB027_MAX_CANDIDATE_AGE_SECONDS","5.0"))
        self.last_persist=0.0;self.persist_modes={}

    def open(self):return [x for x in self.positions["positions"] if x.get("status")=="OPEN"]

    def _amount(self,rows,side):
        q=[f(x.get("quote")) for x in rows if x["side"]==side and f(x.get("quote"))>0]
        return sum(q) if q else float(sum(x["side"]==side for x in rows))

    def _pattern(self,share,accel,unique,momentum,age):
        sb="B3" if share>=.90 else "B2" if share>=.80 else "B1"
        ab="A3" if accel>=4 else "A2" if accel>=2 else "A1"
        ub="U3" if unique>=12 else "U2" if unique>=8 else "U1"
        mb="M3" if momentum>=.08 else "M2" if momentum>=.04 else "M1"
        gb="G0" if age<0 else "G1" if age<60 else "G2" if age<300 else "G3"
        return "|".join((sb,ab,ub,mb,gb))

    def _formation(self,key,now,birth_age):
        xs=list(self.hist[key])
        if len(xs)<8:return None,"TOO_FEW_EVENTS"
        last=xs[-1];w2=[x for x in xs if x["t"]>=last["t"]-2];w5=[x for x in xs if x["t"]>=last["t"]-5];prev=[x for x in xs if last["t"]-12<=x["t"]<last["t"]-2]
        if len(w5)<8:return None,"TOO_FEW_5S_EVENTS"
        b2,s2=self._amount(w2,"BUY"),self._amount(w2,"SELL");b5,s5=self._amount(w5,"BUY"),self._amount(w5,"SELL");bp=self._amount(prev,"BUY")
        share2=b2/(b2+s2) if b2+s2 else .5;share5=b5/(b5+s5) if b5+s5 else .5
        accel=min(5.0,(b2/2)/(bp/10+1e-9)) if bp>0 else (2.0 if b2>0 else 0)
        buys=[x for x in w5 if x["side"]=="BUY"];traders=[x["trader"] for x in buys if x.get("trader")]
        coverage=len(traders)/len(buys) if buys else 0;unique=len(set(traders)) if coverage>=.5 else len(buys)
        by=Counter()
        for x in buys:
            if x.get("trader"):by[x["trader"]]+=x["quote"] if x["quote"]>0 else 1
        total=sum(by.values());largest=max(by.values())/total if total else 0
        p0=f(w5[0]["price"]);p1=f(last["price"]);momentum=p1/p0-1 if p0>0 else 0
        if share5<.58 or unique<3 or momentum<-.01:return None,"NO_BASE_PRESSURE"
        reasons=[]
        arrival=now-last["t"]
        if last["side"]!="BUY":reasons.append("LAST_NOT_BUY")
        if share2<.68:reasons.append("BUY_SHARE_2S")
        if share5<.62:reasons.append("BUY_SHARE_5S")
        if accel<1.10:reasons.append("PRESSURE_ACCEL")
        if unique<4:reasons.append("BUYER_BREADTH")
        if coverage>=.5 and largest>.45:reasons.append("BUYER_CONCENTRATION")
        if momentum<.01:reasons.append("NO_PRICE_CONFIRMATION")
        if momentum>.12:reasons.append("FORMATION_ALREADY_CHASED")
        if arrival<0 or arrival>self.max_signal_arrival:reasons.append("SIGNAL_ARRIVAL_LATE")
        if birth_age<0:reasons.append("LIFECYCLE_UNKNOWN")
        blocked,why=self.failure.blocked(last["token"])
        if blocked:reasons.append(why)
        c={"candidate_id":"C-"+uuid.uuid4().hex[:16],"market":last["market"],"token":last["token"],"family":last["family"],
           "signal_event_t":last["t"],"signal_arrival_unix":now,"signal_arrival_seconds":arrival,"signal_price":p1,
           "birth_age_seconds":birth_age,"buy_share_2s":share2,"buy_share_5s":share5,"pressure_accel":accel,
           "unique_buyers_5s":unique,"buyer_identity_coverage":coverage,"largest_buyer_share":largest,
           "momentum_5s":momentum,"early_buyers":sorted(set(traders))[:30],"formation_reasons":reasons,
           "trade_eligible":not reasons,"pattern":self._pattern(share2,accel,unique,momentum,birth_age)}
        return c,"CANDIDATE"

    def _confirm(self,c,new_rows,now):
        rows=[x for x in new_rows if (x["market"],x["token"])==(c["market"],c["token"]) and x["t"]>c["signal_event_t"]]
        if len(rows)<3:return None,"CONFIRM_TOO_FEW_EVENTS"
        last=rows[-1];arrival=now-last["t"];age=now-c["signal_arrival_unix"]
        if arrival<0 or arrival>self.max_confirm_arrival:return None,"CONFIRM_SOURCE_LATE"
        # The original 2s/5s pressure thesis must still be current AT ENTRY.
        # A new confirmation print cannot resurrect a signal whose causal window
        # has already expired.
        signal_age=now-c["signal_event_t"]
        if signal_age>self.max_signal_arrival:return None,"ENTRY_SIGNAL_STALE"
        if age>self.max_candidate_age:return None,"CANDIDATE_EXPIRED"
        buys=[x for x in rows if x["side"]=="BUY"];sells=[x for x in rows if x["side"]=="SELL"]
        b=self._amount(rows,"BUY");s=self._amount(rows,"SELL");share=b/(b+s) if b+s else .5
        traders={x["trader"] for x in buys if x.get("trader")}
        unique=len(traders) if traders else len(buys)
        move=last["price"]/c["signal_price"]-1
        peak=max(x["price"] for x in rows);roll=last["price"]/peak-1 if peak>0 else 0
        if last["side"]!="BUY":return None,"CONFIRM_LAST_NOT_BUY"
        if share<.65:return None,"CONFIRM_BUY_SHARE"
        if len(buys)<2 or unique<2:return None,"CONFIRM_BREADTH"
        if move<.005:return None,"CONFIRM_NO_CONTINUATION"
        if move>.06:return None,"CONFIRM_LATE_CHASE"
        if roll<-.02:return None,"CONFIRM_ROLLOVER"
        ps=self.outcomes.pattern_stats(c["pattern"])
        if ps["n"]>=5 and (ps["success_rate"] or 0)<.40:return None,"LEARNED_BAD_PATTERN"
        x=dict(c);x.update({"confirm_event_t":last["t"],"confirm_arrival_seconds":arrival,"confirmation_move":move,
                            "confirmation_buy_share":share,"confirmation_unique_buyers":unique,
                            "entry_signal_age_seconds":now-c["signal_event_t"],"entry_price_reference":last["price"],
                            "pattern_stats":ps})
        return x,"CONFIRMED"

    def _enter(self,s):
        half=self.friction/2;ref=f(s["entry_price_reference"]);entry=ref*(1+half);now=self.clock()
        p={"position_id":"QSB027-"+uuid.uuid4().hex[:16],"status":"OPEN","mode":"PAPER","market":s["market"],"token":s["token"],
           "family":s["family"],"opened_unix":now,"reference_entry_price":ref,"entry_price":entry,"qty":self.notional/entry,
           "notional_usdc":self.notional,"high_water_price":entry,"low_water_price":entry,"last_mark_price":ref,
           "last_mark_unix":now,"signal":dict(s),"profit_lock_armed":False,"evidence_valid":True,"real_money_moved":False}
        self.positions["positions"].append(p);return p

    def _close(self,p,mark,reason,valid=True):
        half=self.friction/2;ref=f(mark,p["last_mark_price"]);exitp=ref*(1-half);net=p["qty"]*exitp-p["notional_usdc"];entry=f(p["entry_price"])
        p.update(status="CLOSED",closed_unix=self.clock(),reference_exit_price=ref,exit_price=exitp,exit_reason=reason,
                 net_pnl_usdc=net,net_return=net/p["notional_usdc"],mfe=f(p["high_water_price"])/entry-1,
                 mae=f(p["low_water_price"])/entry-1,evidence_valid=valid)
        self.ledger["trades"].append(dict(p))
        if valid and net<=0:self.failure.loss(p["token"],net,reason,p["signal"])
        return dict(p)

    def _manage_mark(self,e):
        closed=[];now=self.clock()
        for p in list(self.open()):
            if (p["market"],p["token"])!=(e["market"],e["token"]):continue
            px=f(e["price"]);entry=f(p["entry_price"]);p["last_mark_price"]=px;p["last_mark_unix"]=e["t"]
            p["high_water_price"]=max(f(p["high_water_price"]),px);p["low_water_price"]=min(f(p["low_water_price"]),px)
            ret=px/entry-1;mfe=f(p["high_water_price"])/entry-1;trail=px/f(p["high_water_price"])-1
            if mfe>=.07:p["profit_lock_armed"]=True
            reason=None
            if ret<=-.055:reason="STOP_LOSS"
            elif ret>=.12:reason="TAKE_PROFIT"
            elif p["profit_lock_armed"] and (ret<=.035 or trail<=-.035):reason="PROFIT_LOCK"
            if reason:closed.append(self._close(p,px,reason,True))
        return closed

    def _archive_candidate(self,c,status,reason):
        x=dict(c);x["status"]=status;x["terminal_reason"]=reason;x["terminal_unix"]=self.clock()
        self.candidates["archive"].append(x);self.candidates["archive"]=self.candidates["archive"][-10000:]

    def on_batch(self,events,generation,birth_index):
        now=self.clock();self.batches+=1;new_by_key=defaultdict(list);closed=[]
        # Every exact row is consumed sequentially for marks/outcomes. Entry is never
        # allowed until the entire new generation has been incorporated.
        for e in events:
            age=birth_index.age(e);e=dict(e);e["birth_age_seconds"]=age
            key=(e["market"],e["token"]);self.hist[key].append(e);new_by_key[key].append(e)
            self.last_marks[key]=e["price"];self.last_mark_t[key]=e["t"];self.events+=1
            self.outcomes.update_event(e);closed.extend(self._manage_mark(e))

        entered=[];open_tokens={p["token"] for p in self.open()}
        # First, only candidates born in an OLDER artifact generation can confirm.
        for cid,c in list(self.candidates["active"].items()):
            if int(c["formed_generation"])>=int(generation):continue
            sig,why=self._confirm(c,new_by_key.get((c["market"],c["token"]),[]),now)
            if sig and c.get("trade_eligible"):
                if sig["token"] in open_tokens:why="ALREADY_OPEN"
                elif len(self.open())>=self.max_open:why="POSITION_CAP"
                else:
                    entered.append(self._enter(sig));open_tokens.add(sig["token"]);self.confirmed+=1;why="ENTERED"
            self._archive_candidate(c,"CONFIRMED" if sig else "REJECTED",why)
            self.candidates["active"].pop(cid,None)

        # Then form candidates from this generation. They CANNOT enter now.
        for key in new_by_key:
            if any((x["market"],x["token"])==key for x in self.candidates["active"].values()):continue
            last=self.hist[key][-1];c,why=self._formation(key,now,birth_index.age(last))
            if not c:
                self.rejects[why]+=1;continue
            c["formed_generation"]=int(generation);self.candidates["active"][c["candidate_id"]]=c
            self.outcomes.start(c);self.formed+=1
            for r in c["formation_reasons"]:self.rejects[r]+=1

        self.outcomes.heartbeat(now,self.last_marks)
        self.persist(force=bool(entered or closed or events))
        return entered,closed

    def heartbeat(self):
        now=self.clock();closed=[]
        self.outcomes.heartbeat(now,self.last_marks)
        for p in list(self.open()):
            age=now-f(p["opened_unix"])
            if age<self.max_hold:continue
            key=(p["market"],p["token"]);mark=f(self.last_marks.get(key),p["last_mark_price"])
            fresh=now-f(self.last_mark_t.get(key),0)<=10
            closed.append(self._close(p,mark,"MAX_HOLD" if fresh else "DATA_GAP_ABORT",fresh))
        # Expire candidates without ever converting a stale signal into an entry.
        for cid,c in list(self.candidates["active"].items()):
            if now-f(c["signal_arrival_unix"])>self.max_candidate_age:
                self._archive_candidate(c,"REJECTED","NO_FRESH_CONFIRMATION");self.candidates["active"].pop(cid,None)
                self.rejects["NO_FRESH_CONFIRMATION"]+=1
        self.persist(force=bool(closed));return closed

    def stats(self):
        valid=[x for x in self.ledger["trades"] if x.get("evidence_valid",True)];wins=sum(f(x.get("net_pnl_usdc"))>0 for x in valid)
        net=sum(f(x.get("net_pnl_usdc")) for x in valid)
        fin=self.outcomes.data["finalized"];h10=[x for x in fin if x["horizons"].get("10")]
        shadow_success=sum(x["horizons"]["10"]["mfe"]>=.05 and x["horizons"]["10"]["return"]>=.03 for x in h10)
        return {"events":self.events,"batches":self.batches,"candidates_formed":self.formed,"candidates_active":len(self.candidates["active"]),
                "confirmed_entries":self.confirmed,"open":len(self.open()),"closed_valid":len(valid),"wins":wins,
                "losses":len(valid)-wins,"net_pnl_usdc":net,"data_gap_aborts":len(self.ledger["trades"])-len(valid),
                "shadow_10s_samples":len(h10),"shadow_10s_success_rate":shadow_success/len(h10) if h10 else None,
                "rejects":dict(self.rejects),"persistence":dict(self.persist_modes)}
    def persist(self,force=False):
        now=time.monotonic()
        if not force and now-self.last_persist<1:return
        self.persist_modes={
          "positions":write_json(self.positions_path,self.positions),
          "ledger":write_json(self.ledger_path,self.ledger),
          "candidates":write_json(self.candidates_path,self.candidates),
          "outcomes":self.outcomes.save(),
          "status":write_json(self.status_path,self.stats()),
        };self.last_persist=now
