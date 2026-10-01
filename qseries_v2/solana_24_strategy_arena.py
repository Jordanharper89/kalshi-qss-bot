from __future__ import annotations
import json, math, os, time
from collections import Counter, defaultdict
from pathlib import Path
from qseries_v2.solana_money_runner import Config, Row, _atomic_json, _histories, ingest, _now, _second_leg

REVISION="QSB-009-SOLANA-24-STRATEGY-ARENA-V1"

STRATEGIES=(
"SECOND_LEG","MOMENTUM_BREAKOUT","REVERSAL_RECLAIM","STEADY_TREND",
"VOLUME_SURGE_BREAKOUT","VOLUME_PERSISTENCE","BUY_PRESSURE_BREAKOUT","BUY_PRESSURE_ACCELERATION",
"LIQUIDITY_EXPANSION","TURNOVER_SURGE","SHALLOW_PULLBACK_CONTINUATION","DEEP_PULLBACK_RECLAIM",
"HIGHER_LOW_BREAKOUT","RANGE_COMPRESSION_BREAKOUT","FAST_RECLAIM","THREE_BAR_MOMENTUM",
"TREND_PULLBACK","FLOW_CONFIRMATION","PRICE_VOLUME_CONFIRMATION","LIQUIDITY_FLOW_CONFIRMATION",
"VOLATILITY_EXPANSION","LOW_VOL_COMPRESSION_RELEASE","BREAKOUT_HOLD_CONFIRMATION","MULTI_FACTOR_CONFLUENCE",
)

def _f(v,default=0.0):
    try:
        x=float(v);return x if math.isfinite(x) else default
    except Exception:return default

def _ratio(a,b,default=0.0):
    return a/b-1 if b not in (0,None) else default

def _flow(r):
    b=_f(r.buys);s=_f(r.sells);t=b+s
    return b/t if t>0 else .5

def _deltas(rows,attr):
    out=[]
    for a,b in zip(rows[:-1],rows[1:]):
        x=getattr(a,attr);y=getattr(b,attr)
        if x is None or y is None:continue
        out.append(float(y)-float(x))
    return out

def _features(h):
    rows=h[-40:];p=[r.price for r in rows];last=rows[-1]
    n=len(rows);w5=p[-5:] if n>=5 else p;w8=p[-8:] if n>=8 else p;w12=p[-12:] if n>=12 else p
    ret1=_ratio(p[-1],p[-2]) if n>=2 else 0
    ret3=_ratio(p[-1],p[-4]) if n>=4 else 0
    ret5=_ratio(p[-1],p[-6]) if n>=6 else 0
    ret8=_ratio(p[-1],p[-9]) if n>=9 else 0
    hi8=max(w8);lo8=min(w8);hi12=max(w12);lo12=min(w12)
    range5=_ratio(max(w5),min(w5)) if min(w5)>0 else 99
    range8=_ratio(hi8,lo8) if lo8>0 else 99
    breakout5=_ratio(p[-1],max(p[-6:-1])) if n>=6 else 0
    breakout8=_ratio(p[-1],max(p[-9:-1])) if n>=9 else 0
    dd8=1-p[-1]/hi8 if hi8 else 0
    rebound8=_ratio(p[-1],lo8) if lo8 else 0
    up5=sum(1 for a,b in zip(w5[:-1],w5[1:]) if b>a)
    vol_d=_deltas(rows[-8:],"volume");buy_d=_deltas(rows[-8:],"buys");sell_d=_deltas(rows[-8:],"sells")
    dv=sum(max(0,x) for x in vol_d[-3:]) if vol_d else 0
    dv_prev=sum(max(0,x) for x in vol_d[-6:-3]) if len(vol_d)>=6 else 0
    db=sum(max(0,x) for x in buy_d[-3:]) if buy_d else 0
    ds=sum(max(0,x) for x in sell_d[-3:]) if sell_d else 0
    flow_delta=db/(db+ds) if db+ds>0 else _flow(last)
    liq=_f(last.liquidity)
    liq_prev=_f(rows[-4].liquidity) if n>=4 else liq
    liq_growth=_ratio(liq,liq_prev) if liq_prev>0 else 0
    turnover=dv/liq if liq>0 else 0
    recent_rets=[_ratio(b,a) for a,b in zip(w8[:-1],w8[1:])]
    abs_recent=sum(abs(x) for x in recent_rets[-3:])
    abs_prev=sum(abs(x) for x in recent_rets[-6:-3]) if len(recent_rets)>=6 else 0
    vol_expand=abs_recent/(abs_prev+1e-9)
    high_i=max(range(len(w12)),key=w12.__getitem__);low_after=min(w12[high_i:]) if high_i<len(w12) else w12[-1]
    pullback=1-low_after/max(w12) if max(w12)>0 else 0
    rebound=_ratio(p[-1],low_after) if low_after>0 else 0
    return {"n":n,"last":last,"p":p,"ret1":ret1,"ret3":ret3,"ret5":ret5,"ret8":ret8,
            "range5":range5,"range8":range8,"breakout5":breakout5,"breakout8":breakout8,
            "dd8":dd8,"rebound8":rebound8,"up5":up5,"flow":_flow(last),"flow_delta":flow_delta,
            "dv":dv,"dv_prev":dv_prev,"vol_accel":dv/(dv_prev+1e-9) if dv_prev>0 else (2.0 if dv>0 else 0),
            "liq":liq,"liq_growth":liq_growth,"turnover":turnover,"vol_expand":vol_expand,
            "pullback":pullback,"rebound":rebound,"hi12":hi12,"lo12":lo12}

def _sig(name,F,score,extra=None):
    r=F["last"];d={"strategy":name,"market":r.market,"token":r.token,"family":r.family,
        "signal_unix":r.t,"price":r.price,"score":max(0.0,min(1.0,float(score))),
        "liquidity":r.liquidity,"source_file":r.source_file}
    if extra:d.update(extra)
    return d

def detect(name,h,cfg):
    if name=="SECOND_LEG":
        s,reason=_second_leg(h,cfg)
        if s:s=dict(s);s["strategy"]=name
        return s,reason
    F=_features(h)
    if F["n"]<8:return None,"TOO_FEW_POINTS"
    if not F["last"].token:return None,"NO_TOKEN_IDENTITY"
    if _now()-F["last"].t>cfg.max_signal_age_seconds:return None,"STALE"
    if F["liq"] and F["liq"]<3000:return None,"LOW_LIQUIDITY"
    r1,r3,r5,r8=F["ret1"],F["ret3"],F["ret5"],F["ret8"];flow=F["flow_delta"]
    ok=False;score=0.0;why="NO_SETUP"
    if name=="MOMENTUM_BREAKOUT":
        ok=F["breakout5"]>.015 and r3>.04 and r5<.60 and flow>.52
        score=.35*min(1,r3/.15)+.30*min(1,F["breakout5"]/.08)+.20*min(1,max(0,flow-.5)/.25)+.15*min(1,max(0,r5)/.30);why="NO_BREAKOUT"
    elif name=="REVERSAL_RECLAIM":
        ok=.12<=F["pullback"]<=.65 and F["rebound"]>.06 and F["breakout5"]>0 and flow>.50
        score=.35*min(1,F["pullback"]/.4)+.35*min(1,F["rebound"]/.25)+.15*min(1,max(0,r1)/.08)+.15*min(1,max(0,flow-.5)/.25);why="NO_REVERSAL"
    elif name=="STEADY_TREND":
        ok=r8>.10 and F["up5"]>=3 and r1>0 and F["dd8"]<.10
        score=.45*min(1,r8/.30)+.25*min(1,max(0,r1)/.06)+.20*min(1,max(0,flow-.5)/.25)+.10*min(1,F["up5"]/4);why="NO_TREND"
    elif name=="VOLUME_SURGE_BREAKOUT":
        ok=F["vol_accel"]>1.8 and F["breakout5"]>.01 and r3>.02
        score=.40*min(1,F["vol_accel"]/4)+.35*min(1,F["breakout5"]/.08)+.25*min(1,r3/.12);why="NO_VOLUME_SURGE"
    elif name=="VOLUME_PERSISTENCE":
        ok=F["dv"]>0 and F["dv_prev"]>0 and F["vol_accel"]>.75 and r5>.04 and F["up5"]>=3
        score=.35*min(1,F["vol_accel"]/2)+.40*min(1,r5/.20)+.25*min(1,F["up5"]/4);why="NO_VOLUME_PERSISTENCE"
    elif name=="BUY_PRESSURE_BREAKOUT":
        ok=flow>.62 and F["breakout5"]>.01 and r3>.02
        score=.45*min(1,(flow-.5)/.30)+.35*min(1,F["breakout5"]/.08)+.20*min(1,r3/.10);why="NO_BUY_PRESSURE_BREAKOUT"
    elif name=="BUY_PRESSURE_ACCELERATION":
        ok=flow>.68 and F["flow"]>.60 and r1>0 and r3>.015
        score=.50*min(1,(flow-.5)/.35)+.30*min(1,r3/.10)+.20*min(1,max(0,r1)/.05);why="NO_FLOW_ACCELERATION"
    elif name=="LIQUIDITY_EXPANSION":
        ok=F["liq_growth"]>.04 and r3>.015 and flow>.52
        score=.45*min(1,F["liq_growth"]/.20)+.30*min(1,r3/.10)+.25*min(1,(flow-.5)/.25);why="NO_LIQUIDITY_EXPANSION"
    elif name=="TURNOVER_SURGE":
        ok=F["turnover"]>.015 and r3>.02 and flow>.52
        score=.45*min(1,F["turnover"]/.10)+.30*min(1,r3/.12)+.25*min(1,(flow-.5)/.25);why="NO_TURNOVER_SURGE"
    elif name=="SHALLOW_PULLBACK_CONTINUATION":
        ok=r8>.10 and .03<=F["dd8"]<=.12 and r1>.015 and flow>.52
        score=.35*min(1,r8/.30)+.30*min(1,F["dd8"]/.12)+.20*min(1,r1/.06)+.15*min(1,(flow-.5)/.25);why="NO_SHALLOW_PULLBACK"
    elif name=="DEEP_PULLBACK_RECLAIM":
        ok=.15<=F["pullback"]<=.45 and F["rebound"]>.10 and F["breakout5"]>0
        score=.35*min(1,F["pullback"]/.35)+.40*min(1,F["rebound"]/.30)+.25*min(1,F["breakout5"]/.08);why="NO_DEEP_RECLAIM"
    elif name=="HIGHER_LOW_BREAKOUT":
        lows=[min(F["p"][-8:-4]),min(F["p"][-4:])]
        ok=lows[1]>lows[0]*1.01 and F["breakout5"]>.01 and flow>.52
        score=.40*min(1,(lows[1]/lows[0]-1)/.10)+.35*min(1,F["breakout5"]/.08)+.25*min(1,(flow-.5)/.25);why="NO_HIGHER_LOW_BREAKOUT"
    elif name=="RANGE_COMPRESSION_BREAKOUT":
        prior=F["p"][-8:-2]
        pr=(max(prior)/min(prior)-1) if len(prior)>=4 else 99
        ok=pr<.08 and F["breakout5"]>.015 and r1>.015
        score=.35*min(1,max(0,.08-pr)/.08)+.40*min(1,F["breakout5"]/.08)+.25*min(1,r1/.06);why="NO_COMPRESSION_BREAKOUT"
    elif name=="FAST_RECLAIM":
        ok=F["pullback"]>.08 and F["rebound"]>.08 and r3>.04 and F["up5"]>=3
        score=.30*min(1,F["pullback"]/.30)+.35*min(1,F["rebound"]/.25)+.20*min(1,r3/.12)+.15*min(1,F["up5"]/4);why="NO_FAST_RECLAIM"
    elif name=="THREE_BAR_MOMENTUM":
        rs=[_ratio(F["p"][i],F["p"][i-1]) for i in range(len(F["p"])-2,len(F["p"]))]
        ok=r3>.05 and all(x>0 for x in rs) and flow>.52
        score=.55*min(1,r3/.15)+.25*min(1,(flow-.5)/.25)+.20*min(1,F["up5"]/4);why="NO_THREE_BAR_MOMENTUM"
    elif name=="TREND_PULLBACK":
        ok=r8>.08 and .02<=F["dd8"]<=.10 and r1>0 and F["up5"]>=3
        score=.40*min(1,r8/.25)+.25*min(1,F["dd8"]/.10)+.20*min(1,r1/.05)+.15*min(1,F["up5"]/4);why="NO_TREND_PULLBACK"
    elif name=="FLOW_CONFIRMATION":
        ok=flow>.60 and F["flow"]>.58 and r5>.04
        score=.45*min(1,(flow-.5)/.30)+.25*min(1,(F["flow"]-.5)/.25)+.30*min(1,r5/.15);why="NO_FLOW_CONFIRMATION"
    elif name=="PRICE_VOLUME_CONFIRMATION":
        ok=r5>.05 and F["dv"]>0 and F["vol_accel"]>1.0 and F["up5"]>=3
        score=.40*min(1,r5/.20)+.35*min(1,F["vol_accel"]/3)+.25*min(1,F["up5"]/4);why="NO_PRICE_VOLUME_CONFIRMATION"
    elif name=="LIQUIDITY_FLOW_CONFIRMATION":
        ok=F["liq_growth"]>.015 and flow>.60 and r3>.015
        score=.35*min(1,F["liq_growth"]/.15)+.40*min(1,(flow-.5)/.30)+.25*min(1,r3/.10);why="NO_LIQ_FLOW_CONFIRMATION"
    elif name=="VOLATILITY_EXPANSION":
        ok=F["vol_expand"]>1.5 and r3>.03 and r1>0
        score=.45*min(1,F["vol_expand"]/4)+.35*min(1,r3/.15)+.20*min(1,r1/.06);why="NO_VOLATILITY_EXPANSION"
    elif name=="LOW_VOL_COMPRESSION_RELEASE":
        ok=F["range5"]<.06 and F["breakout8"]>.015 and r1>.015
        score=.35*min(1,max(0,.06-F["range5"])/.06)+.40*min(1,F["breakout8"]/.08)+.25*min(1,r1/.06);why="NO_LOW_VOL_RELEASE"
    elif name=="BREAKOUT_HOLD_CONFIRMATION":
        if F["n"]>=10:
            prev=max(F["p"][-10:-3]);held=min(F["p"][-3:])>prev*.99
            ok=held and F["p"][-1]>prev*1.01 and flow>.52
            score=.45*min(1,max(0,F["p"][-1]/prev-1)/.08)+.30*min(1,(flow-.5)/.25)+.25*(1 if held else 0);why="NO_BREAKOUT_HOLD"
    elif name=="MULTI_FACTOR_CONFLUENCE":
        factors=[r3>.03,F["breakout5"]>.01,flow>.57,F["vol_accel"]>1.2,F["liq_growth"]>0,F["up5"]>=3]
        c=sum(factors);ok=c>=4
        score=c/6;why="NO_CONFLUENCE"
    if not ok:return None,why
    s=_sig(name,F,score,{"flow":flow,"r1":r1,"r3":r3,"r5":r5,"r8":r8,
        "volume_accel":F["vol_accel"],"liquidity_growth":F["liq_growth"],"turnover":F["turnover"]})
    threshold=.45 if name!="SECOND_LEG" else cfg.min_score
    if s["score"]<threshold:return s,"SCORE_BELOW_GATE"
    return s,"READY"

class Arena:
    def __init__(self,root:Path,state_rel=Path("runtime_state/qseries/solana_24_strategy_arena")):
        self.root=Path(root).resolve();self.cfg=Config.from_env();self.state=self.root/state_rel
        self.ledger_path=self.state/"ledger.json";self.positions_path=self.state/"positions.json";self.status_path=self.state/"status.json"
        try:self.ledger=json.loads(self.ledger_path.read_text())
        except Exception:self.ledger={"trades":[]}
        try:self.positions=json.loads(self.positions_path.read_text())
        except Exception:self.positions={"positions":[]}
        self.notional=float(os.getenv("QSB009_NOTIONAL_USDC","5"))
        self.friction=float(os.getenv("QSB009_ROUNDTRIP_FRICTION","0.03"))
        self.stop=float(os.getenv("QSB009_STOP_LOSS","0.08"))
        self.tp=float(os.getenv("QSB009_TAKE_PROFIT","0.15"))
        self.trail=float(os.getenv("QSB009_TRAILING_STOP","0.07"))
        self.max_hold=float(os.getenv("QSB009_MAX_HOLD_SECONDS","300"))
        self.cooldown=float(os.getenv("QSB009_COOLDOWN_SECONDS","90"))
        self.max_open_per_strategy=int(os.getenv("QSB009_MAX_OPEN_PER_STRATEGY","2"))

    def _open(self):return [p for p in self.positions["positions"] if p.get("status")=="OPEN"]

    def _manage(self,latest):
        closed=[];half=self.friction/2
        for p in self.positions["positions"]:
            if p.get("status")!="OPEN":continue
            r=latest.get(p["market"])
            if r is None:continue
            px=r.price;entry=float(p["entry_price"]);p["high_water_price"]=max(float(p["high_water_price"]),px)
            ret=px/entry-1;trail=px/p["high_water_price"]-1;age=_now()-float(p["opened_unix"]);reason=None
            if ret<=-self.stop:reason="STOP_LOSS"
            elif ret>=self.tp:reason="TAKE_PROFIT"
            elif p["high_water_price"]>=entry*1.08 and trail<=-self.trail:reason="TRAILING_STOP"
            elif age>=self.max_hold:reason="MAX_HOLD"
            if not reason:continue
            exit_px=px*(1-half);gross=p["qty"]*px-self.notional;net=p["qty"]*exit_px-self.notional
            p.update({"status":"CLOSED","closed_unix":_now(),"reference_exit_price":px,"exit_price":exit_px,
                "exit_reason":reason,"gross_pnl_usdc":gross,
                "modeled_friction_usdc":gross-net+float(p.get("modeled_entry_friction_usdc") or 0),
                "net_pnl_usdc":net,"net_return":net/self.notional})
            self.ledger["trades"].append(dict(p));closed.append(dict(p))
        _atomic_json(self.positions_path,self.positions);_atomic_json(self.ledger_path,self.ledger);return closed

    def _recent(self,strategy,market):
        ts=0.0
        for p in self.positions["positions"]:
            if p.get("strategy")==strategy and p.get("market")==market:ts=max(ts,float(p.get("opened_unix") or 0))
        return _now()-ts<self.cooldown

    def _enter(self,s):
        half=self.friction/2;entry=s["price"]*(1+half)
        p={"position_id":f'PAPER-{s["strategy"]}-{int(_now()*1000)}',"mode":"PAPER","status":"OPEN",
           "strategy":s["strategy"],"market":s["market"],"token":s["token"],"family":s["family"],
           "opened_unix":_now(),"reference_entry_price":s["price"],"entry_price":entry,
           "high_water_price":entry,"notional_usdc":self.notional,"qty":self.notional/entry,
           "modeled_entry_friction_usdc":self.notional*half,"signal":s}
        self.positions["positions"].append(p);_atomic_json(self.positions_path,self.positions);return p

    def cycle(self,progress=False):
        rows,files=ingest(self.root,self.cfg,progress=progress);hist=_histories(rows);latest={m:h[-1] for m,h in hist.items() if h}
        closed=self._manage(latest);reasons=Counter();ready=[];evaluated=Counter()
        for market,h in hist.items():
            for name in STRATEGIES:
                evaluated[name]+=1;s,reason=detect(name,h,self.cfg);reasons[f"{name}:{reason}"]+=1
                if s and reason=="READY":ready.append(s)
        ready.sort(key=lambda x:x["score"],reverse=True);entered=[]
        open_counts=Counter(p["strategy"] for p in self._open())
        for s in ready:
            if open_counts[s["strategy"]]>=self.max_open_per_strategy:continue
            if self._recent(s["strategy"],s["market"]):continue
            entered.append(self._enter(s));open_counts[s["strategy"]]+=1
        trades=self.ledger["trades"];by={}
        for name in STRATEGIES:
            xs=[t for t in trades if t.get("strategy")==name];wins=sum(_f(t.get("net_pnl_usdc"))>0 for t in xs);net=sum(_f(t.get("net_pnl_usdc")) for t in xs)
            by[name]={"closed":len(xs),"wins":wins,"losses":len(xs)-wins,
                      "win_rate":wins/len(xs) if xs else None,"net_pnl_usdc":net,
                      "avg_net_usdc":net/len(xs) if xs else None}
        ranked=sorted(({"strategy":k,**v} for k,v in by.items()),key=lambda x:(x["net_pnl_usdc"],x["closed"]),reverse=True)
        status={"revision":REVISION,"strategy_count":len(STRATEGIES),"source_rows":len(rows),"markets_watched":len(hist),
                "tokens_watched":len({r.token for r in rows if r.token}),"ready_signals":len(ready),
                "entered_this_cycle":len(entered),"closed_this_cycle":len(closed),"open_positions":len(self._open()),
                "closed_trades":len(trades),"arena_net_pnl_usdc":sum(_f(t.get("net_pnl_usdc")) for t in trades),
                "by_strategy":by,"leaderboard":ranked,"evaluation_counts":dict(evaluated),
                "why_no_trade":dict(reasons.most_common(24)),"paper_only":True,"real_money_moved":False,
                "profitability_claimed":False}
        _atomic_json(self.status_path,status);return status
