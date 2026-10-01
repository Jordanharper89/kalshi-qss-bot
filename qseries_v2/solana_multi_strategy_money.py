from __future__ import annotations
import json, os
from collections import Counter
from qseries_v2.solana_money_runner import MoneyRunner, _histories, ingest, _second_leg, _atomic_json, _now

REVISION="QSB-007-SOLANA-UNIVERSAL-MULTI-STRATEGY-V1"

def _liq_ok(last):
    try:return last.liquidity is None or float(last.liquidity)>=float(os.getenv("QSB007_MIN_LIQUIDITY_USD","5000"))
    except Exception:return False

def _flow(last):
    if last.buys is None or last.sells is None:return 0.5
    t=float(last.buys)+float(last.sells)
    return float(last.buys)/t if t>0 else 0.5

def _momentum_breakout(h,cfg):
    if len(h)<8:return None,"TOO_FEW_POINTS"
    rows=h[-30:];p=[x.price for x in rows];last=rows[-1]
    if not _liq_ok(last):return None,"LOW_LIQUIDITY"
    current=p[-1];prior=p[-6:-1]
    if current<=max(prior)*1.015:return None,"NO_BREAKOUT"
    ret3=current/p[-4]-1
    if ret3<0.04:return None,"WEAK_MOMENTUM"
    extension=current/min(p[-8:])-1
    if extension>0.60:return None,"TOO_EXTENDED"
    flow=_flow(last)
    if flow<0.52:return None,"WEAK_BUY_FLOW"
    score=min(1.0,0.35*min(1,ret3/.15)+0.30*min(1,(current/max(prior)-1)/.08)+0.20*min(1,max(0,flow-.5)/.25)+0.15*min(1,max(0,extension)/.30))
    s={"strategy":"MOMENTUM_BREAKOUT","market":last.market,"token":last.token,"family":last.family,
       "signal_unix":last.t,"price":current,"score":score,"momentum":ret3,
       "breakout":current/max(prior)-1,"flow":flow,"liquidity":last.liquidity,"source_file":last.source_file}
    if not last.token:return s,"NO_TOKEN_IDENTITY"
    if _now()-last.t>cfg.max_signal_age_seconds:return s,"STALE"
    if score<max(.45,cfg.min_score-.08):return s,"SCORE_BELOW_GATE"
    return s,"READY"

def _reversal_reclaim(h,cfg):
    if len(h)<10:return None,"TOO_FEW_POINTS"
    rows=h[-40:];p=[x.price for x in rows];last=rows[-1]
    if not _liq_ok(last):return None,"LOW_LIQUIDITY"
    hi=max(p[:-3]);hi_i=p.index(hi)
    tail=p[hi_i+1:]
    if len(tail)<4:return None,"NO_REVERSAL_PATH"
    lo=min(tail);lo_i=p.index(lo,hi_i+1)
    dd=1-lo/hi
    if dd<.12 or dd>.65:return None,"REVERSAL_DRAWDOWN_GATE"
    current=p[-1];rebound=current/lo-1
    if rebound<.06:return None,"NO_REVERSAL_REBOUND"
    if current<=max(p[-4:-1]):return None,"NO_SHORT_RECLAIM"
    flow=_flow(last)
    score=min(1.0,0.35*min(1,dd/.40)+0.35*min(1,rebound/.25)+0.15*min(1,max(0,current/p[-2]-1)/.08)+0.15*min(1,max(0,flow-.5)/.25))
    s={"strategy":"REVERSAL_RECLAIM","market":last.market,"token":last.token,"family":last.family,
       "signal_unix":last.t,"price":current,"score":score,"drawdown":dd,"rebound":rebound,
       "flow":flow,"liquidity":last.liquidity,"source_file":last.source_file}
    if not last.token:return s,"NO_TOKEN_IDENTITY"
    if _now()-last.t>cfg.max_signal_age_seconds:return s,"STALE"
    if score<max(.45,cfg.min_score-.08):return s,"SCORE_BELOW_GATE"
    return s,"READY"

def _steady_trend(h,cfg):
    if len(h)<10:return None,"TOO_FEW_POINTS"
    rows=h[-20:];p=[x.price for x in rows];last=rows[-1]
    if not _liq_ok(last):return None,"LOW_LIQUIDITY"
    current=p[-1];ret=current/p[-8]-1
    if ret<.10:return None,"NO_TREND"
    peak=p[-8];worst=0.0
    for x in p[-7:]:
        peak=max(peak,x);worst=min(worst,x/peak-1)
    if worst<-.10:return None,"TREND_TOO_CHOPPY"
    if current<=p[-2]:return None,"TREND_STALLED"
    flow=_flow(last)
    score=min(1.0,0.45*min(1,ret/.30)+0.25*min(1,max(0,current/p[-2]-1)/.06)+0.20*min(1,max(0,flow-.5)/.25)+0.10*min(1,max(0,.10+worst)/.10))
    s={"strategy":"STEADY_TREND","market":last.market,"token":last.token,"family":last.family,
       "signal_unix":last.t,"price":current,"score":score,"trend_return":ret,
       "max_pullback":worst,"flow":flow,"liquidity":last.liquidity,"source_file":last.source_file}
    if not last.token:return s,"NO_TOKEN_IDENTITY"
    if _now()-last.t>cfg.max_signal_age_seconds:return s,"STALE"
    if score<max(.45,cfg.min_score-.08):return s,"SCORE_BELOW_GATE"
    return s,"READY"

DETECTORS=(("SECOND_LEG",_second_leg),("MOMENTUM_BREAKOUT",_momentum_breakout),
           ("REVERSAL_RECLAIM",_reversal_reclaim),("STEADY_TREND",_steady_trend))

class EnsembleMoneyRunner(MoneyRunner):
    def cycle(self,progress=True):
        rows,files=ingest(self.root,self.cfg,progress=progress)
        hist=_histories(rows);latest={m:h[-1] for m,h in hist.items() if h}
        closed=self._manage(latest)
        reasons=Counter();setups=[]
        for _,h in hist.items():
            for name,fn in DETECTORS:
                sig,reason=fn(h,self.cfg)
                reasons[f"{name}:{reason}"]+=1
                if sig:
                    sig=dict(sig);sig["gate_reason"]=reason;setups.append(sig)
        setups.sort(key=lambda s:s["score"],reverse=True)
        entered=[];capacity=max(0,self.cfg.max_open_positions-len(self._open_positions()))
        used_markets={p["market"] for p in self._open_positions()}
        for s in setups:
            if capacity<=0:break
            if s["gate_reason"]!="READY" or s["market"] in used_markets:continue
            if self._already_traded(s):
                reasons[f'{s["strategy"]}:DUPLICATE_SIGNAL']+=1;continue
            entered.append(self._enter(s));used_markets.add(s["market"]);capacity-=1
        trades=self.ledger["trades"];wins=sum(float(t.get("net_pnl_usdc") or 0)>0 for t in trades)
        losses=sum(float(t.get("net_pnl_usdc") or 0)<0 for t in trades)
        gross=sum(float(t.get("gross_pnl_usdc") or 0) for t in trades)
        friction=sum(float(t.get("modeled_friction_usdc") or 0) for t in trades)
        net=sum(float(t.get("net_pnl_usdc") or 0) for t in trades)
        by_strategy={}
        for t in trades:
            z=by_strategy.setdefault(t.get("strategy","UNKNOWN"),{"closed":0,"wins":0,"net":0.0})
            z["closed"]+=1;z["wins"]+=int(float(t.get("net_pnl_usdc") or 0)>0);z["net"]+=float(t.get("net_pnl_usdc") or 0)
        status={"revision":REVISION,"unix":_now(),"source_files":len(files),"source_rows":len(rows),
                "markets_watched":len(hist),"tokens_watched":len({r.token for r in rows if r.token}),
                "setups_found":len(setups),"ready_setups":sum(s["gate_reason"]=="READY" for s in setups),
                "trades_entered_this_cycle":len(entered),"trades_closed_this_cycle":len(closed),
                "open_positions":len(self._open_positions()),"closed_trades":len(trades),"wins":wins,"losses":losses,
                "win_rate":wins/len(trades) if trades else None,"gross_pnl_usdc":gross,
                "modeled_friction_usdc":friction,"net_pnl_usdc":net,
                "profitability_proven":len(trades)>=20 and net>0 and wins/len(trades)>.50,
                "why_no_trade":dict(reasons),"strategy_results":by_strategy,
                "top_setups":setups[:10],"paper_only":True,"real_money_moved":False}
        _atomic_json(self.status_path,status);return status
