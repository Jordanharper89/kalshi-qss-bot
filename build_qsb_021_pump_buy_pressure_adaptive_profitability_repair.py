from pathlib import Path
import py_compile, shutil

ROOT=Path.cwd()
ARENA=ROOT/"qseries_v2/solana_champion_challenger_arena.py"
RUNTIME=ROOT/"qseries_v2/solana_qsb013_runtime.py"
RUN=ROOT/"run_qsb_013_solana_universal_champion_challenger.py"

for p in (ARENA,RUNTIME,RUN):
    if not p.is_file():
        raise SystemExit("[FAIL] missing QSB-013 dependency: "+str(p.relative_to(ROOT)))

arena_old=ARENA.read_text(encoding="utf-8",errors="ignore")
runtime_old=RUNTIME.read_text(encoding="utf-8",errors="ignore")
if "ChampionChallengerArena" not in arena_old or "QSB-013" not in runtime_old:
    raise SystemExit("[FAIL] QSB-013 source contract not recognized; refusing blind overwrite")

for src in (ARENA,RUNTIME):
    bak=src.with_suffix(src.suffix+".pre_qsb021")
    if not bak.exists():
        shutil.copy2(src,bak)

ARENA_TEXT=r"""
from __future__ import annotations
import json, math, os, statistics
from collections import Counter, defaultdict
from pathlib import Path

from qseries_v2.solana_24_strategy_arena import Arena, STRATEGIES, detect
from qseries_v2.solana_money_runner import _histories, ingest, _atomic_json, _now

REVISION="QSB-021-PUMP-BUY-PRESSURE-ADAPTIVE-PROFITABILITY-V1"
TARGET="BUY_PRESSURE_ACCELERATION"
PUMP_FAMILIES={"PUMP_FUN","PUMP_SWAP","PUMPSWAP","PUMP","PUMP.FUN"}
FEATURES=("flow5","pressure_accel","unique_buyers10","sell_ratio10","momentum10","birth_age_seconds","base_score")

def _f(v,d=0.0):
    try:
        x=float(v)
        return x if math.isfinite(x) else float(d)
    except Exception:
        return float(d)

def _pump_family(v):
    s=str(v or "").upper().replace("-","_").replace(" ","_")
    return s in PUMP_FAMILIES or "PUMP" in s

def _walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            if isinstance(v,(dict,list)):
                yield from _walk(v)
    elif isinstance(obj,list):
        for v in obj:
            if isinstance(v,(dict,list)):
                yield from _walk(v)

def _median(xs,default=0.0):
    xs=[_f(x) for x in xs]
    return statistics.median(xs) if xs else float(default)

class ChampionChallengerArena(Arena):
    def __init__(self,root:Path,physical_root:Path|None=None):
        super().__init__(root,state_rel=Path("runtime_state/qseries/solana_24_strategy_arena"))
        self.physical_root=Path(physical_root or root).resolve()
        self.min_closed=int(os.getenv("QSB013_MIN_CLOSED","4"))
        self.min_win=float(os.getenv("QSB013_MIN_WIN_RATE","0.55"))
        self.challenge_score=float(os.getenv("QSB013_CHALLENGE_SCORE","0.60"))
        self.max_champion_open=int(os.getenv("QSB013_MAX_CHAMPION_OPEN","3"))
        self.max_challenger_open=int(os.getenv("QSB013_MAX_CHALLENGER_OPEN","6"))
        self.max_token_positions=int(os.getenv("QSB013_MAX_OPEN_PER_TOKEN","1"))

        self.pump_state=self.physical_root/"runtime_state/qseries/qsb013_pump_buy_pressure"
        self.pump_positions_path=self.pump_state/"positions.json"
        self.pump_ledger_path=self.pump_state/"ledger.json"
        self.pump_learning_path=self.pump_state/"learning.json"
        self.pump_status_path=self.pump_state/"status.json"
        self.pump_state.mkdir(parents=True,exist_ok=True)
        try:self.pump_positions=json.loads(self.pump_positions_path.read_text(encoding="utf-8"))
        except Exception:self.pump_positions={"positions":[]}
        try:self.pump_ledger=json.loads(self.pump_ledger_path.read_text(encoding="utf-8"))
        except Exception:self.pump_ledger={"trades":[]}

        self.pump_notional=float(os.getenv("QSB021_NOTIONAL_USDC","5"))
        self.pump_friction=float(os.getenv("QSB021_ROUNDTRIP_FRICTION","0.03"))
        self.pump_stop=float(os.getenv("QSB021_STOP_LOSS","0.08"))
        self.pump_tp=float(os.getenv("QSB021_TAKE_PROFIT","0.14"))
        self.pump_trail=float(os.getenv("QSB021_TRAILING_STOP","0.06"))
        self.pump_max_hold=float(os.getenv("QSB021_MAX_HOLD_SECONDS","90"))
        self.pump_cooldown=float(os.getenv("QSB021_COOLDOWN_SECONDS","12"))
        self.max_pump_open=int(os.getenv("QSB021_MAX_PUMP_OPEN","12"))
        self.min_exact_trades=int(os.getenv("QSB021_MIN_EXACT_TRADES_10S","3"))
        self.min_unique_buyers=int(os.getenv("QSB021_MIN_UNIQUE_BUYERS_10S","2"))
        self.base_admission=float(os.getenv("QSB021_BASE_ADMISSION_SCORE","0.58"))
        self.signal_max_age=float(os.getenv("QSB021_SIGNAL_MAX_AGE_SECONDS","20"))

    def stats(self):
        out={}
        for name in STRATEGIES:
            if name==TARGET:
                xs=self.pump_ledger["trades"]
            else:
                xs=[t for t in self.ledger["trades"] if t.get("strategy")==name]
            wins=sum(_f(t.get("net_pnl_usdc"))>0 for t in xs)
            net=sum(_f(t.get("net_pnl_usdc")) for t in xs)
            out[name]={"closed":len(xs),"wins":wins,"losses":len(xs)-wins,
                       "win_rate":wins/len(xs) if xs else None,
                       "net":net,"avg":net/len(xs) if xs else None}
        return out

    def champions(self,stats):
        # BUY_PRESSURE is now a dedicated Pump lane, never part of shared champion capacity.
        return {n for n,s in stats.items()
                if n!=TARGET and s["closed"]>=self.min_closed and s["net"]>0
                and (s["win_rate"] or 0)>=self.min_win and (s["avg"] or 0)>0}

    def _pump_open(self):
        return [p for p in self.pump_positions["positions"] if p.get("status")=="OPEN"]

    def _pump_recent(self,token):
        ts=0.0
        for p in self.pump_positions["positions"]:
            if p.get("token")==token:
                ts=max(ts,_f(p.get("opened_unix")))
        return _now()-ts<self.pump_cooldown

    def _exact_tape_rows(self):
        paths=[
            self.physical_root/"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json",
            self.physical_root/"runtime_state/solana_opportunities/solana_scanner/pump_exact_trade_economic_path.json",
        ]
        rows=[]
        for p in paths:
            if not p.is_file(): continue
            try:obj=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
            except Exception:continue
            for d in _walk(obj):
                token=d.get("token_address") or d.get("token_mint")
                market=d.get("market_address") or d.get("pair_address")
                price=_f(d.get("effective_price"))
                t=_f(d.get("observed_unix") or d.get("trade_observed_unix") or d.get("block_time") or d.get("event_timestamp"))
                side=str(d.get("side") or "").upper()
                if not token or not market or price<=0 or t<=0 or side not in ("BUY","SELL"):
                    continue
                rows.append({
                    "token":str(token),"market":str(market),"price":price,"t":t,"side":side,
                    "quote":abs(_f(d.get("quote_amount") or d.get("quote_quantity") or d.get("quote_amount_lamports"))),
                    "trader":str(d.get("trader") or ""),
                    "birth_age_seconds":_f(d.get("birth_age_seconds"),-1),
                    "family":"PUMP_FUN",
                    "source":"EXACT_PUMP_TRADE_TAPE",
                })
        rows.sort(key=lambda x:x["t"])
        return rows

    def _exact_signals(self):
        rows=self._exact_tape_rows()
        if not rows:return []
        by=defaultdict(list)
        for r in rows:by[(r["market"],r["token"])].append(r)
        out=[]
        wall=_now()
        for (market,token),xs in by.items():
            last=xs[-1];latest_t=last["t"]
            if wall-latest_t>self.signal_max_age:continue
            w5=[x for x in xs if x["t"]>=latest_t-5]
            w10=[x for x in xs if x["t"]>=latest_t-10]
            prev=[x for x in xs if latest_t-20<=x["t"]<latest_t-5]
            if len(w10)<self.min_exact_trades:continue
            def amt(rr,side):
                q=sum(x["quote"] for x in rr if x["side"]==side)
                return q if q>0 else float(sum(x["side"]==side for x in rr))
            b5,s5=amt(w5,"BUY"),amt(w5,"SELL")
            b10,s10=amt(w10,"BUY"),amt(w10,"SELL")
            bp=amt(prev,"BUY")
            flow5=b5/(b5+s5) if b5+s5>0 else 0.5
            sell_ratio=s10/(b10+s10) if b10+s10>0 else 0.5
            current_rate=b5/5.0
            prev_rate=bp/15.0 if bp>0 else 0.0
            pressure_accel=current_rate/(prev_rate+1e-9) if current_rate>0 else 0.0
            pressure_accel=min(5.0,pressure_accel)
            buyers={x["trader"] for x in w10 if x["side"]=="BUY" and x["trader"]}
            unique=len(buyers) if buyers else sum(x["side"]=="BUY" for x in w10)
            p0=w10[0]["price"];p1=w10[-1]["price"]
            momentum=p1/p0-1 if p0>0 else 0.0
            birth=max((x["birth_age_seconds"] for x in w10 if x["birth_age_seconds"]>=0),default=-1)
            score=(
                .34*max(0.0,min(1.0,(flow5-.50)/.35))+
                .24*max(0.0,min(1.0,(pressure_accel-1.0)/2.0))+
                .18*max(0.0,min(1.0,(unique-1)/6.0))+
                .14*max(0.0,min(1.0,momentum/.08))+
                .10*max(0.0,min(1.0,(1.0-sell_ratio-.50)/.35))
            )
            if flow5<.64 or pressure_accel<1.05 or unique<self.min_unique_buyers or momentum<=0:
                continue
            out.append({
                "strategy":TARGET,"market":market,"token":token,"family":"PUMP_FUN",
                "signal_unix":latest_t,"price":p1,"score":score,"base_score":score,
                "flow5":flow5,"pressure_accel":pressure_accel,"unique_buyers10":unique,
                "sell_ratio10":sell_ratio,"momentum10":momentum,"birth_age_seconds":birth,
                "source_file":"EXACT_PUMP_TRADE_TAPE",
            })
        return out

    def _learning(self):
        xs=self.pump_ledger["trades"][-120:]
        wins=[t for t in xs if _f(t.get("net_pnl_usdc"))>0]
        losses=[t for t in xs if _f(t.get("net_pnl_usdc"))<=0]
        data={"sample":len(xs),"wins":len(wins),"losses":len(losses),
              "win_rate":len(wins)/len(xs) if xs else None,
              "net":sum(_f(t.get("net_pnl_usdc")) for t in xs),
              "promoted":[],"demoted":[],"feature_stats":{},
              "admission_score":self.base_admission,
              "stop_loss":self.pump_stop,"take_profit":self.pump_tp,
              "trailing_stop":self.pump_trail,"max_hold_seconds":self.pump_max_hold}
        if len(xs)>=6 and len(wins)>=4 and len(losses)>=2:
            for feat in FEATURES:
                w=[_f((t.get("signal") or {}).get(feat)) for t in wins]
                l=[_f((t.get("signal") or {}).get(feat)) for t in losses]
                wm=sum(w)/len(w);lm=sum(l)/len(l)
                scale=max(abs(wm),abs(lm),1e-6)
                sep=(wm-lm)/scale
                data["feature_stats"][feat]={"win_mean":wm,"loss_mean":lm,"separation":sep}
                if feat in ("sell_ratio10","birth_age_seconds"):
                    sep=-sep
                if sep>.12:data["promoted"].append(feat)
                elif sep<-.12:data["demoted"].append(feat)
            wr=data["win_rate"] or 0.0
            if data["net"]<=0 or wr<.50:data["admission_score"]=min(.72,self.base_admission+.08)
            elif wr>=.65 and data["net"]>0:data["admission_score"]=max(.52,self.base_admission-.03)

        if len(xs)>=10 and wins and losses:
            winner_mfe=[_f(t.get("mfe")) for t in wins if t.get("mfe") is not None]
            loser_mae=[abs(_f(t.get("mae"))) for t in losses if t.get("mae") is not None]
            if winner_mfe:
                data["take_profit"]=max(.09,min(.24,_median(winner_mfe,self.pump_tp)*.70))
            if loser_mae:
                data["stop_loss"]=max(.05,min(.11,_median(loser_mae,self.pump_stop)*.80))
        _atomic_json(self.pump_learning_path,data)
        return data

    def _adaptive_score(self,s,learning):
        score=_f(s.get("base_score") or s.get("score"))
        fs=learning.get("feature_stats") or {}
        for feat in learning.get("promoted") or []:
            st=fs.get(feat) or {};wm=_f(st.get("win_mean"));lm=_f(st.get("loss_mean"))
            v=_f(s.get(feat))
            higher_good=feat not in ("sell_ratio10","birth_age_seconds")
            if higher_good and v>=wm:score+=.025
            elif not higher_good and v<=wm:score+=.025
            elif higher_good and v<=lm:score-=.025
            elif not higher_good and v>=lm:score-=.025
        for feat in learning.get("demoted") or []:
            st=fs.get(feat) or {};wm=_f(st.get("win_mean"));lm=_f(st.get("loss_mean"))
            v=_f(s.get(feat))
            higher_good=feat not in ("sell_ratio10","birth_age_seconds")
            if higher_good and v>=lm:score-=.015
            elif not higher_good and v<=lm:score-=.015
        return max(0.0,min(1.0,score))

    def _enter_pump(self,s):
        half=self.pump_friction/2;entry=_f(s["price"])*(1+half)
        p={"position_id":f'PUMP-BP-{int(_now()*1000)}',"mode":"PAPER","status":"OPEN",
           "strategy":TARGET,"market":s["market"],"token":s["token"],"family":s.get("family","PUMP_FUN"),
           "opened_unix":_now(),"reference_entry_price":s["price"],"entry_price":entry,
           "high_water_price":entry,"low_water_price":entry,"notional_usdc":self.pump_notional,
           "qty":self.pump_notional/entry,"modeled_entry_friction_usdc":self.pump_notional*half,
           "signal":dict(s)}
        self.pump_positions["positions"].append(p)
        _atomic_json(self.pump_positions_path,self.pump_positions)
        return p

    def _manage_pump(self,latest_price,learning):
        closed=[];half=self.pump_friction/2
        stop=_f(learning.get("stop_loss"),self.pump_stop)
        tp=_f(learning.get("take_profit"),self.pump_tp)
        trail=_f(learning.get("trailing_stop"),self.pump_trail)
        max_hold=_f(learning.get("max_hold_seconds"),self.pump_max_hold)
        for p in self.pump_positions["positions"]:
            if p.get("status")!="OPEN":continue
            px=_f(latest_price.get((p["market"],p["token"])))
            if px<=0:continue
            entry=_f(p["entry_price"]);p["high_water_price"]=max(_f(p.get("high_water_price"),entry),px)
            p["low_water_price"]=min(_f(p.get("low_water_price"),entry),px)
            ret=px/entry-1;tr=px/p["high_water_price"]-1;age=_now()-_f(p["opened_unix"])
            reason=None
            if ret<=-stop:reason="STOP_LOSS"
            elif ret>=tp:reason="TAKE_PROFIT"
            elif p["high_water_price"]>=entry*1.07 and tr<=-trail:reason="TRAILING_STOP"
            elif age>=max_hold:reason="MAX_HOLD"
            if not reason:continue
            exit_px=px*(1-half);gross=p["qty"]*px-self.pump_notional;net=p["qty"]*exit_px-self.pump_notional
            mfe=p["high_water_price"]/entry-1;mae=p["low_water_price"]/entry-1
            p.update(status="CLOSED",closed_unix=_now(),reference_exit_price=px,exit_price=exit_px,
                     exit_reason=reason,gross_pnl_usdc=gross,
                     modeled_friction_usdc=gross-net+_f(p.get("modeled_entry_friction_usdc")),
                     net_pnl_usdc=net,net_return=net/self.pump_notional,mfe=mfe,mae=mae)
            self.pump_ledger["trades"].append(dict(p));closed.append(dict(p))
        _atomic_json(self.pump_positions_path,self.pump_positions)
        _atomic_json(self.pump_ledger_path,self.pump_ledger)
        return closed

    def _fallback_pump_signals(self,hist):
        out=[]
        for _,h in hist.items():
            if not h or not _pump_family(h[-1].family):continue
            s,reason=detect(TARGET,h,self.cfg)
            if s and reason=="READY":
                s=dict(s);s["base_score"]=_f(s.get("score"));s["source_file"]="QSB013_FALLBACK_HISTORY"
                s.setdefault("flow5",_f(s.get("flow")));s.setdefault("pressure_accel",_f(s.get("volume_accel"),1.0))
                s.setdefault("unique_buyers10",0);s.setdefault("sell_ratio10",max(0.0,1.0-_f(s.get("flow"),.5)))
                s.setdefault("momentum10",_f(s.get("r3")));s.setdefault("birth_age_seconds",-1)
                out.append(s)
        return out

    def cycle(self,progress=False):
        rows,files=ingest(self.root,self.cfg,progress=progress)
        hist=_histories(rows);latest={m:h[-1] for m,h in hist.items() if h}

        # Manage legacy non-Pump strategy book unchanged.
        closed=self._manage(latest)

        # Exact Pump tape is the primary BUY_PRESSURE source; history is fallback only.
        exact_rows=self._exact_tape_rows()
        latest_pump={}
        for r in exact_rows:latest_pump[(r["market"],r["token"])]=r["price"]
        for _,h in hist.items():
            if h and _pump_family(h[-1].family):
                latest_pump.setdefault((h[-1].market,h[-1].token),h[-1].price)

        learning=self._learning()
        pump_closed=self._manage_pump(latest_pump,learning)
        learning=self._learning()

        pump_ready=self._exact_signals()
        source_mode="EXACT_PUMP_TRADE_TAPE"
        if not pump_ready:
            pump_ready=self._fallback_pump_signals(hist)
            source_mode="FALLBACK_QSB013_HISTORY"

        dedup={}
        for s in pump_ready:
            k=(s.get("market"),s.get("token"))
            if k not in dedup or _f(s.get("score"))>_f(dedup[k].get("score")):dedup[k]=s
        pump_ready=list(dedup.values())
        for s in pump_ready:s["adaptive_score"]=self._adaptive_score(s,learning)
        pump_ready.sort(key=lambda x:_f(x.get("adaptive_score")),reverse=True)

        pump_open=self._pump_open()
        pump_tokens=Counter(p.get("token") for p in pump_open if p.get("token"))
        pump_entered=[]
        for s in pump_ready:
            if len(self._pump_open())>=self.max_pump_open:break
            token=s.get("token")
            if token and pump_tokens[token]>=1:continue
            if token and self._pump_recent(token):continue
            if _f(s.get("adaptive_score"))<_f(learning.get("admission_score"),self.base_admission):continue
            pump_entered.append(self._enter_pump(s))
            if token:pump_tokens[token]+=1

        # Generic champion/challenger arena continues, but BUY_PRESSURE is removed from it.
        stats=self.stats();champions=self.champions(stats)
        ready=[];reasons=Counter()
        for _,h in hist.items():
            for name in STRATEGIES:
                if name==TARGET:continue
                sig,reason=detect(name,h,self.cfg);reasons[f"{name}:{reason}"]+=1
                if sig and reason=="READY":ready.append(sig)
        ready.sort(key=lambda x:x["score"],reverse=True)

        open_now=self._open()
        token_counts=Counter(p.get("token") for p in open_now if p.get("token"))
        champion_open=sum(1 for p in open_now if p.get("strategy") in champions)
        challenger_open=len(open_now)-champion_open
        entered=[];champion_entries=0;challenger_entries=0

        for s in ready:
            name=s["strategy"];token=s.get("token")
            if token and token_counts[token]>=self.max_token_positions:continue
            if self._recent(name,s["market"]):continue
            if name in champions:
                if champion_open+champion_entries>=self.max_champion_open:continue
                lane="CHAMPION"
            else:
                if challenger_open+challenger_entries>=self.max_challenger_open:continue
                if _f(s.get("score"))<self.challenge_score:continue
                lane="CHALLENGER"
            s=dict(s);s["selection_lane"]=lane
            entered.append(self._enter(s))
            if lane=="CHAMPION":champion_entries+=1
            else:challenger_entries+=1
            if token:token_counts[token]+=1

        trades=self.ledger["trades"];stats=self.stats();champions=self.champions(stats)
        ranked=sorted(({"strategy":k,**v} for k,v in stats.items()),key=lambda x:(x["net"],x["closed"]),reverse=True)

        pstats=stats[TARGET]
        learning=self._learning()
        pump_status={
            "source_mode":source_mode,"ready":len(pump_ready),"entered":len(pump_entered),"closed_this_cycle":len(pump_closed),
            "open":len(self._pump_open()),"closed":pstats["closed"],"wins":pstats["wins"],"losses":pstats["losses"],
            "win_rate":pstats["win_rate"],"net":pstats["net"],"milestone":pstats["wins"]>=10 and pstats["net"]>0,
            "learning":learning,"max_open":self.max_pump_open,
        }
        _atomic_json(self.pump_status_path,pump_status)

        status={"revision":REVISION,"strategy_count":len(STRATEGIES),"source_rows":len(rows),"markets_watched":len(hist),
                "tokens_watched":len({r.token for r in rows if r.token}),"champions":sorted(champions),
                "ready_signals":len(ready),"entered_this_cycle":len(entered),"champion_entries":champion_entries,
                "challenger_entries":challenger_entries,"closed_this_cycle":len(closed),"open_positions":len(self._open()),
                "closed_trades":len(trades),"arena_net_pnl_usdc":sum(_f(t.get("net_pnl_usdc")) for t in trades),
                "leaderboard":ranked,"pump_buy_pressure":pump_status,"paper_only":True,"real_money_moved":False}
        _atomic_json(self.status_path,status);return status
"""

RUNTIME_TEXT=r"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from qseries_v2.solana_windows_safe_provider import WindowsSafeUniversalProvider
from qseries_v2.solana_qsb013_burst import BurstRadar,expand_hot_mints
from qseries_v2.solana_champion_challenger_arena import ChampionChallengerArena

STATE=Path("runtime_state/qseries/qsb013_universal")
WORKSPACE=STATE/"workspace"
FEED=Path("runtime_state/solana_opportunities/qsb013_feed.jsonl")
OLD=Path("runtime_state/qseries/solana_24_strategy_runtime/workspace/runtime_state/qseries/solana_24_strategy_arena")

def _seed(root,workspace):
    dst=workspace/"runtime_state/qseries/solana_24_strategy_arena";dst.mkdir(parents=True,exist_ok=True)
    for n in ("ledger.json","positions.json"):
        s=root/OLD/n;d=dst/n
        if s.exists() and not d.exists():d.write_text(s.read_text(encoding="utf-8",errors="ignore"),encoding="utf-8")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--once",action="store_true");ap.add_argument("--sleep",type=float,default=2)
    a=ap.parse_args();root=Path(a.root).resolve();workspace=root/WORKSPACE;feed=workspace/FEED;feed.parent.mkdir(parents=True,exist_ok=True)
    _seed(root,workspace)
    stable=WindowsSafeUniversalProvider(root,max_tokens=48,active_tokens=20,timeout=8,refresh_seconds=90)
    stable.cache_path=root/STATE/"universe_cache.json";stable.cache_path.parent.mkdir(parents=True,exist_ok=True)
    burst=BurstRadar(root);arena=ChampionChallengerArena(workspace,physical_root=root)
    while True:
        try:ss=stable.snapshot();stable_rows=list(ss.get("rows") or [])
        except Exception:stable_rows=[]
        try:bs=burst.scan(4,8);hot_rows=expand_hot_mints(bs.get("hot_mints") or [],8)
        except Exception:bs={"raw_rows":0,"new_signatures":0,"hydrated":0,"hot_mints":[],"family_counts":{}};hot_rows=[]
        merged={}
        for r in stable_rows+hot_rows:
            if r.get("market_address"):merged[r["market_address"]]=r
        rows=list(merged.values())
        with feed.open("a",encoding="utf-8") as f:
            for r in rows:f.write(json.dumps(r,sort_keys=True)+"\n")
        s=arena.cycle(False);p=s["pump_buy_pressure"];L=p["learning"]
        print("="*126);print(" QSB-021 QSB-013 PUMP BUY_PRESSURE ADAPTIVE PROFITABILITY REPAIR");print("="*126)
        print(f"[BURST] raw={bs.get('raw_rows')} sigs={bs.get('new_signatures')} hydrated={bs.get('hydrated')} hot_mints={len(bs.get('hot_mints') or [])} hot_rows={len(hot_rows)}")
        print("[BURST FAMILIES]",json.dumps(bs.get("family_counts") or {},sort_keys=True))
        print(f"[WATCHING] markets={s['markets_watched']} tokens={s['tokens_watched']} rows={s['source_rows']}")
        print(f"[PUMP BUY_PRESSURE] source={p['source_mode']} ready={p['ready']} entered={p['entered']} closed={p['closed_this_cycle']} open={p['open']} total_closed={p['closed']} wins={p['wins']} losses={p['losses']} NET=${p['net']:.4f} milestone={p['milestone']}")
        print(f"[BUY_PRESSURE LEARNING] sample={L['sample']} win_rate={L['win_rate']} admission={L['admission_score']:.3f} promoted={L['promoted']} demoted={L['demoted']}")
        print(f"[ADAPTIVE EXITS] stop={L['stop_loss']:.3f} tp={L['take_profit']:.3f} trail={L['trailing_stop']:.3f} max_hold={L['max_hold_seconds']:.0f}s")
        print(f"[OTHER STRATEGIES] ready={s['ready_signals']} entered={s['entered_this_cycle']} closed={s['closed_this_cycle']} open={s['open_positions']}")
        print("[MODE] ONE RUNTIME | PUMP BUY_PRESSURE HAS INDEPENDENT PAPER BOOK | PAPER_ONLY | REAL_MONEY_MOVED=False")
        if p["milestone"]:print("[PASS] 10 PUMP BUY_PRESSURE WINS + POSITIVE NET")
        if a.once:break
        time.sleep(max(1,a.sleep))
if __name__=="__main__":main()
"""

TEST_TEXT=r"""
import json,os,tempfile,time,unittest
from pathlib import Path
from qseries_v2.solana_champion_challenger_arena import ChampionChallengerArena,TARGET

class T(unittest.TestCase):
    def _arena(self,td):
        return ChampionChallengerArena(Path(td)/"workspace",physical_root=Path(td))

    def test_exact_pump_signal_and_nonpump_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json"
            p.parent.mkdir(parents=True)
            now=time.time()
            rows=[]
            for i in range(8):
                rows.append({"token_address":"T","market_address":"M","effective_price":1+i*.01,
                    "observed_unix":now-8+i,"side":"BUY" if i>=2 else "SELL",
                    "quote_amount":10+i*5,"trader":"W"+str(i),"birth_age_seconds":20+i})
            p.write_text(json.dumps({"rows":rows}),encoding="utf-8")
            a=self._arena(td);sig=a._exact_signals()
            self.assertGreaterEqual(len(sig),1)
            self.assertEqual(sig[0]["strategy"],TARGET)
            self.assertEqual(sig[0]["family"],"PUMP_FUN")
            self.assertGreater(sig[0]["unique_buyers10"],1)

    def test_independent_book_not_blocked_by_legacy_open(self):
        with tempfile.TemporaryDirectory() as td:
            a=self._arena(td)
            a.positions={"positions":[{"status":"OPEN","strategy":"OTHER","token":"X"+str(i)} for i in range(7)]}
            s={"strategy":TARGET,"market":"M","token":"T","family":"PUMP_FUN","price":1.0,"score":.9,
               "base_score":.9,"flow5":.8,"pressure_accel":2.0,"unique_buyers10":5,
               "sell_ratio10":.2,"momentum10":.05,"birth_age_seconds":20}
            a._enter_pump(s)
            self.assertEqual(len(a._pump_open()),1)
            self.assertEqual(len(a._open()),7)

    def test_winner_loser_learning_changes_gate(self):
        with tempfile.TemporaryDirectory() as td:
            a=self._arena(td)
            trades=[]
            for i in range(6):
                trades.append({"net_pnl_usdc":1.0,"mfe":.20,"mae":-.03,"signal":{
                    "flow5":.82,"pressure_accel":2.5,"unique_buyers10":7,"sell_ratio10":.18,
                    "momentum10":.06,"birth_age_seconds":25,"base_score":.85}})
            for i in range(2):
                trades.append({"net_pnl_usdc":-.5,"mfe":.03,"mae":-.12,"signal":{
                    "flow5":.58,"pressure_accel":.9,"unique_buyers10":2,"sell_ratio10":.48,
                    "momentum10":.005,"birth_age_seconds":160,"base_score":.55}})
            a.pump_ledger={"trades":trades}
            L=a._learning()
            self.assertGreaterEqual(len(L["promoted"]),1)
            self.assertLessEqual(L["admission_score"],a.base_admission)
            winner_like={"base_score":.70,"flow5":.84,"pressure_accel":2.8,"unique_buyers10":8,
                         "sell_ratio10":.15,"momentum10":.07,"birth_age_seconds":20}
            self.assertGreater(a._adaptive_score(winner_like,L),.70)

    def test_ten_win_positive_net_milestone_math(self):
        with tempfile.TemporaryDirectory() as td:
            a=self._arena(td)
            a.pump_ledger={"trades":[{"net_pnl_usdc":.25,"signal":{}} for _ in range(10)]}
            s=a.stats()[TARGET]
            self.assertEqual(s["wins"],10)
            self.assertGreater(s["net"],0)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

ARENA.write_text(ARENA_TEXT,encoding="utf-8")
RUNTIME.write_text(RUNTIME_TEXT,encoding="utf-8")
TEST=ROOT/"test_qsb_021_pump_buy_pressure_adaptive_profitability_repair.py"
TEST.write_text(TEST_TEXT,encoding="utf-8")
for p in (ARENA,RUNTIME,TEST,RUN):
    py_compile.compile(str(p),doraise=True)

print("[PASS] QSB-013 arena rebuilt in place:",ARENA.relative_to(ROOT))
print("[PASS] QSB-013 runtime rebuilt in place:",RUNTIME.relative_to(ROOT))
print("[PASS] backup:",ARENA.with_suffix(ARENA.suffix+".pre_qsb021").relative_to(ROOT))
print("[PASS] backup:",RUNTIME.with_suffix(RUNTIME.suffix+".pre_qsb021").relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[REPAIR] BUY_PRESSURE is Pump/PumpSwap-only and removed from shared champion capacity")
print("[REPAIR] exact Pump trade tape is primary; QSB-013 history is fallback")
print("[REPAIR] independent 12-slot paper book; per-token dedupe; 12s cooldown")
print("[LEARNING] winner-vs-loser feature attribution changes admission score and bounded exits")
print("[GATE] 10 wins + positive net milestone")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")
