
from __future__ import annotations
import asyncio, importlib, inspect, json, math, os, statistics, threading, time
from collections import Counter, defaultdict
from pathlib import Path

from qseries_v2.solana_24_strategy_arena import Arena, STRATEGIES, detect
from qseries_v2.solana_money_runner import _histories, ingest, _atomic_json, _now

REVISION="QSB-022-PUMP-ECOSYSTEM-END-TO-END-PROFITABILITY-V1"
TARGET="BUY_PRESSURE_ACCELERATION"
WSOL="So11111111111111111111111111111111111111112"
USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
EXCLUDE={WSOL,USDC}

FEATURES=(
    "flow3","flow8","pressure_accel","unique_buyers8","largest_buyer_share",
    "sell_ratio8","momentum8","birth_age_seconds","wallet_quality","base_score"
)

TRADE_PATHS=(
    "runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json",
    "runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json",
    "runtime_state/solana_opportunities/universal_trade_tape/multidex_universal_economic_tape.json",
    "runtime_state/solana_opportunities/solana_scanner/pump_exact_trade_economic_path.json",
    "runtime_state/solana_opportunities/universal_trade_tape/universal_trade_tape.json",
    "runtime_state/solana_opportunities/universal_trade_tape/pump_enriched_trade_tape.json",
)

BIRTH_PATHS=(
    "runtime_state/solana_opportunities/universal_launch_scanner/canonical_universal_birth_events.json",
    "runtime_state/solana_opportunities/universal_launch_scanner/pump_create_v2_decoded_births.json",
    "runtime_state/solana_opportunities/universal_launch_scanner/pump_create_v2_live_capture.json",
)

CONTEXT_PATHS=(
    "runtime_state/solana_opportunities/universal_launch_scanner/pump_bonding_curve_states.json",
    "runtime_state/solana_opportunities/universal_launch_scanner/pump_short_horizon_curve_follow.json",
    "runtime_state/solana_opportunities/universal_launch_scanner/pump_sampled_path_outcomes.json",
)

PUMPFUN_CHAIN=(
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_033_universal_trade_tape_normalizer",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_034_restart_safe_universal_trade_tape_store",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_035_pump_trade_raw_transaction_hydration",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_036_exact_trader_base_amount_resolver",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_037_quote_amount_evidence_audit",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_038_enriched_universal_trade_tape",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_040_pump_trade_event_exact_decoder",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_041_pump_trade_event_reconciliation",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_042_pump_exact_economic_trade_tape",
    "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_043_pump_exact_flow_feature_rebuild",
)

def _f(v,d=0.0):
    try:
        x=float(v)
        return x if math.isfinite(x) else float(d)
    except Exception:
        return float(d)

def _walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            if isinstance(v,(dict,list)): yield from _walk(v)
    elif isinstance(obj,list):
        for v in obj:
            if isinstance(v,(dict,list)): yield from _walk(v)

def _median(xs,default=0.0):
    xs=[_f(x) for x in xs]
    return statistics.median(xs) if xs else float(default)

def _family(v,program_id=""):
    s=str(v or "").upper().replace("-","_").replace(" ","_")
    if "PUMP_SWAP" in s or "PUMPSWAP" in s or str(program_id)=="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA":
        return "PUMP_SWAP"
    if "PUMP" in s or str(program_id)=="6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P":
        return "PUMP_FUN"
    return ""

def _call_root(module_name,root,names=("write","build","repair","resolve")):
    m=importlib.import_module(module_name)
    last=None
    for n in names:
        fn=getattr(m,n,None)
        if not callable(fn): continue
        try:
            sig=inspect.signature(fn)
            if len(sig.parameters)==0:return fn()
            return fn(root)
        except TypeError as e:
            last=e
            continue
    if last: raise last
    raise AttributeError("no compatible root callable")

class PumpSourceWorker:
    def __init__(self,root:Path):
        self.root=Path(root).resolve()
        self.state=self.root/"runtime_state/qseries/qsb013_pump_buy_pressure/source_worker.json"
        self.stop_event=threading.Event()
        self.thread=None
        self.cycles=0
        self.last={}
        self.fun_seconds=float(os.getenv("QSB022_PUMPFUN_CAPTURE_SECONDS","8"))
        self.router_seconds=float(os.getenv("QSB022_PUMPSWAP_ROUTER_SECONDS","4"))
        self.sleep_seconds=float(os.getenv("QSB022_SOURCE_WORKER_SLEEP_SECONDS","1"))

    def _pumpfun(self):
        d={"capture":False,"chain_ok":0,"chain_errors":[]}
        mod=importlib.import_module(
            "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_032_live_pump_curve_trade_tape_capture"
        )
        run=getattr(mod,"run")
        run(self.root,seconds=self.fun_seconds,max_trades=300)
        d["capture"]=True
        for name in PUMPFUN_CHAIN:
            try:
                _call_root(name,self.root)
                d["chain_ok"]+=1
            except Exception as e:
                d["chain_errors"].append(name.rsplit(".",1)[-1]+":"+type(e).__name__)
        return d

    def _pumpswap(self):
        d={"router_rows":0,"identity":False,"economic":False,"repair":False,"errors":[]}
        try:
            m=importlib.import_module(
                "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router"
            )
            cap=getattr(m,"capture")
            ret=asyncio.run(cap(seconds=self.router_seconds,max_rows=2500))
            if isinstance(ret,dict):
                d["router_rows"]=len(ret.get("rows") or [])
                p=self.root/"runtime_state/solana_opportunities/universal_trade_tape/multidex_live_event_router.json"
                _atomic_json(p,ret)
        except Exception as e:
            d["errors"].append("046b:"+type(e).__name__)
        try:
            _call_root(
                "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_047c_batched_retry_safe_multidex_identity_resolver",
                self.root,names=("write","resolve")
            )
            d["identity"]=True
        except Exception as e:d["errors"].append("047c:"+type(e).__name__)
        try:
            _call_root(
                "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_048b_shared_universal_economic_normalizer",
                self.root
            )
            d["economic"]=True
        except Exception as e:d["errors"].append("048b:"+type(e).__name__)
        try:
            _call_root(
                "qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_101d_pumpswap_048b_direct_rematerialization_repair",
                self.root
            )
            d["repair"]=True
        except Exception as e:d["errors"].append("101d:"+type(e).__name__)
        return d

    def once(self):
        self.cycles+=1
        fun={};swap={}
        try:fun=self._pumpfun()
        except Exception as e:fun={"capture":False,"chain_ok":0,"chain_errors":["032:"+type(e).__name__]}
        try:swap=self._pumpswap()
        except Exception as e:swap={"router_rows":0,"identity":False,"economic":False,"repair":False,"errors":["worker:"+type(e).__name__]}
        self.last={"revision":REVISION,"cycles":self.cycles,"pumpfun":fun,"pumpswap":swap,
                   "updated_unix":time.time(),"execution_authority":False}
        _atomic_json(self.state,self.last)
        return self.last

    def _loop(self):
        while not self.stop_event.is_set():
            self.once()
            self.stop_event.wait(max(.1,self.sleep_seconds))

    def start(self):
        if self.thread and self.thread.is_alive():return
        self.thread=threading.Thread(target=self._loop,name="QSB022PumpSourceWorker",daemon=True)
        self.thread.start()

class ChampionChallengerArena(Arena):
    def __init__(self,root:Path,physical_root:Path|None=None,start_worker=True):
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
        self.pump_wallet_path=self.pump_state/"wallet_learning.json"
        self.pump_status_path=self.pump_state/"status.json"
        self.pump_state.mkdir(parents=True,exist_ok=True)

        try:self.pump_positions=json.loads(self.pump_positions_path.read_text(encoding="utf-8"))
        except Exception:self.pump_positions={"positions":[]}
        try:self.pump_ledger=json.loads(self.pump_ledger_path.read_text(encoding="utf-8"))
        except Exception:self.pump_ledger={"trades":[]}
        try:self.wallet_learning=json.loads(self.pump_wallet_path.read_text(encoding="utf-8"))
        except Exception:self.wallet_learning={"wallets":{}}

        self.pump_notional=float(os.getenv("QSB022_NOTIONAL_USDC","5"))
        self.pump_friction=float(os.getenv("QSB022_ROUNDTRIP_FRICTION","0.03"))
        self.pump_stop=float(os.getenv("QSB022_STOP_LOSS","0.08"))
        self.pump_tp=float(os.getenv("QSB022_TAKE_PROFIT","0.14"))
        self.pump_trail=float(os.getenv("QSB022_TRAILING_STOP","0.06"))
        self.pump_max_hold=float(os.getenv("QSB022_MAX_HOLD_SECONDS","75"))
        self.pump_cooldown=float(os.getenv("QSB022_COOLDOWN_SECONDS","8"))
        self.max_pump_open=int(os.getenv("QSB022_MAX_PUMP_OPEN","16"))
        self.min_exact_trades=int(os.getenv("QSB022_MIN_EXACT_TRADES_8S","3"))
        self.min_unique_buyers=int(os.getenv("QSB022_MIN_UNIQUE_BUYERS_8S","2"))
        self.base_admission=float(os.getenv("QSB022_BASE_ADMISSION_SCORE","0.52"))
        self.signal_max_age=float(os.getenv("QSB022_SIGNAL_MAX_AGE_SECONDS","15"))
        self.source_fresh=float(os.getenv("QSB022_SOURCE_FRESH_SECONDS","35"))

        self.worker=PumpSourceWorker(self.physical_root)
        disabled=os.getenv("QSB022_DISABLE_LIVE_WORKER","0")=="1"
        if start_worker and not disabled:self.worker.start()

    def stats(self):
        out={}
        for name in STRATEGIES:
            xs=self.pump_ledger["trades"] if name==TARGET else [t for t in self.ledger["trades"] if t.get("strategy")==name]
            wins=sum(_f(t.get("net_pnl_usdc"))>0 for t in xs)
            net=sum(_f(t.get("net_pnl_usdc")) for t in xs)
            out[name]={"closed":len(xs),"wins":wins,"losses":len(xs)-wins,
                       "win_rate":wins/len(xs) if xs else None,
                       "net":net,"avg":net/len(xs) if xs else None}
        return out

    def champions(self,stats):
        return {n for n,s in stats.items()
                if n!=TARGET and s["closed"]>=self.min_closed and s["net"]>0
                and (s["win_rate"] or 0)>=self.min_win and (s["avg"] or 0)>0}

    def _pump_open(self):
        return [p for p in self.pump_positions["positions"] if p.get("status")=="OPEN"]

    def _pump_recent(self,token):
        ts=0.0
        for p in self.pump_positions["positions"]:
            if p.get("token")==token:ts=max(ts,_f(p.get("opened_unix")))
        return _now()-ts<self.pump_cooldown

    def _birth_map(self):
        out={}
        creators={}
        count=0
        for rel in BIRTH_PATHS:
            p=self.physical_root/rel
            if not p.is_file():continue
            try:obj=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
            except Exception:continue
            for d in _walk(obj):
                fam=_family(d.get("launcher_family") or d.get("source_family") or d.get("family"),d.get("program_id"))
                token=d.get("token_address") or d.get("token_mint")
                t=_f(d.get("observed_unix") or d.get("birth_observed_unix") or d.get("block_time"))
                if not fam or not token or token in EXCLUDE or t<=0:continue
                count+=1
                token=str(token)
                if token not in out or t<out[token]:out[token]=t
                c=d.get("creator") or d.get("deployer") or d.get("user") or d.get("trader")
                if c:creators[token]=str(c)
        return out,creators,count

    def _normalize_trade(self,d,source):
        fam=_family(d.get("venue") or d.get("family"),d.get("program_id"))
        if not fam:return None
        token=d.get("token_address") or d.get("token_mint") or d.get("token")
        market=d.get("market_address") or d.get("pair_address") or d.get("pool")
        price=_f(d.get("effective_price") or d.get("price") or d.get("last_price"))
        t=_f(d.get("observed_unix") or d.get("trade_observed_unix") or d.get("event_timestamp") or d.get("block_time"))
        side=str(d.get("side") or "").upper()
        if not token or str(token) in EXCLUDE or not market or price<=0 or t<=0 or side not in ("BUY","SELL"):
            return None
        quote=abs(_f(d.get("quote_amount") or d.get("quote_quantity") or d.get("quote_amount_lamports")))
        return {
            "token":str(token),"market":str(market),"price":price,"t":t,"side":side,
            "quote":quote,"trader":str(d.get("trader") or ""),
            "birth_age_seconds":_f(d.get("birth_age_seconds"),-1),
            "family":fam,"source":source,
            "trade_id":str(d.get("trade_id") or ""),
            "signature":str(d.get("signature") or d.get("trade_signature") or ""),
            "instruction_index":str(d.get("instruction_index") or ""),
        }

    def _ecosystem_rows(self):
        rows=[];seen=set();source_counts=Counter()
        for rel in TRADE_PATHS:
            p=self.physical_root/rel
            if not p.is_file():continue
            try:obj=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
            except Exception:continue
            for d in _walk(obj):
                r=self._normalize_trade(d,rel)
                if not r:continue
                key=r["trade_id"] or (r["signature"],r["instruction_index"],r["market"],r["token"],r["side"])
                if key in seen:continue
                seen.add(key);rows.append(r);source_counts[rel]+=1
        rows.sort(key=lambda x:x["t"])
        return rows,source_counts

    def _wallet_quality(self,buyers):
        vals=[]
        for w in buyers:
            d=(self.wallet_learning.get("wallets") or {}).get(w)
            if not d or int(d.get("trades") or 0)<2:continue
            wins=int(d.get("wins") or 0);n=int(d.get("trades") or 0);net=_f(d.get("net"))
            q=(wins+1)/(n+2)
            if net<0:q-=.08
            vals.append(max(0.0,min(1.0,q)))
        return sum(vals)/len(vals) if vals else .5

    def _exact_signals(self,rows,births,creators):
        if not rows:return []
        by=defaultdict(list)
        for r in rows:by[(r["market"],r["token"])].append(r)
        out=[];wall=_now()
        for (market,token),xs in by.items():
            last=xs[-1];latest_t=last["t"]
            if abs(wall-latest_t)>self.signal_max_age:continue
            w3=[x for x in xs if x["t"]>=latest_t-3]
            w8=[x for x in xs if x["t"]>=latest_t-8]
            prev=[x for x in xs if latest_t-20<=x["t"]<latest_t-8]
            if len(w8)<self.min_exact_trades:continue

            def amount(rr,side):
                q=sum(x["quote"] for x in rr if x["side"]==side)
                return q if q>0 else float(sum(x["side"]==side for x in rr))

            b3,s3=amount(w3,"BUY"),amount(w3,"SELL")
            b8,s8=amount(w8,"BUY"),amount(w8,"SELL")
            bp=amount(prev,"BUY")
            flow3=b3/(b3+s3) if b3+s3>0 else .5
            flow8=b8/(b8+s8) if b8+s8>0 else .5
            sell_ratio=s8/(b8+s8) if b8+s8>0 else .5
            current_rate=b3/3.0
            prev_rate=bp/12.0 if bp>0 else 0.0
            accel=current_rate/(prev_rate+1e-9) if prev_rate>0 else (2.0 if current_rate>0 else 0.0)
            accel=min(5.0,accel)

            buyer_rows=[x for x in w8 if x["side"]=="BUY"]
            traders=[x["trader"] for x in buyer_rows if x["trader"]]
            unique_buyers=len(set(traders)) if traders else len(buyer_rows)
            by_wallet=Counter()
            for x in buyer_rows:
                if x["trader"]:by_wallet[x["trader"]]+=x["quote"] if x["quote"]>0 else 1.0
            total_b=sum(by_wallet.values())
            largest=max(by_wallet.values())/total_b if total_b>0 else (1.0/unique_buyers if unique_buyers else 1.0)

            p0=w8[0]["price"];p1=w8[-1]["price"];momentum=p1/p0-1 if p0>0 else 0.0
            birth_age=last["birth_age_seconds"]
            if birth_age<0 and token in births:birth_age=max(0.0,latest_t-births[token])
            creator=creators.get(token,"")
            creator_buyer=bool(creator and creator in set(traders))
            wallet_q=self._wallet_quality(set(traders))

            if flow3<.58 or flow8<.56 or unique_buyers<self.min_unique_buyers or momentum<-.01:
                continue
            if largest>.78 or creator_buyer:
                continue
            if not (accel>=1.0 or (birth_age>=0 and birth_age<=30 and flow3>=.65)):
                continue

            score=(
                .23*max(0,min(1,(flow3-.50)/.35))+
                .18*max(0,min(1,(flow8-.50)/.30))+
                .18*max(0,min(1,(accel-1.0)/2.0))+
                .14*max(0,min(1,(unique_buyers-1)/7.0))+
                .10*max(0,min(1,max(0,momentum)/.08))+
                .09*max(0,min(1,(wallet_q-.35)/.45))+
                .08*max(0,min(1,(.78-largest)/.60))
            )
            out.append({
                "strategy":TARGET,"market":market,"token":token,"family":last["family"],
                "signal_unix":latest_t,"price":p1,"score":score,"base_score":score,
                "flow3":flow3,"flow8":flow8,"pressure_accel":accel,
                "unique_buyers8":unique_buyers,"largest_buyer_share":largest,
                "sell_ratio8":sell_ratio,"momentum8":momentum,
                "birth_age_seconds":birth_age,"wallet_quality":wallet_q,
                "creator_buyer":creator_buyer,"early_buyers":sorted(set(traders))[:20],
                "source_file":"QSB022_JOINED_PUMP_ECOSYSTEM",
            })
        return out

    def _learning(self):
        xs=self.pump_ledger["trades"][-160:]
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
                wm=sum(w)/len(w);lm=sum(l)/len(l);scale=max(abs(wm),abs(lm),1e-6)
                sep=(wm-lm)/scale
                higher_good=feat not in ("largest_buyer_share","sell_ratio8","birth_age_seconds")
                judged=sep if higher_good else -sep
                data["feature_stats"][feat]={"win_mean":wm,"loss_mean":lm,"separation":judged}
                if judged>.12:data["promoted"].append(feat)
                elif judged<-.12:data["demoted"].append(feat)
            wr=data["win_rate"] or 0
            if data["net"]<=0 or wr<.50:data["admission_score"]=min(.70,self.base_admission+.08)
            elif wr>=.65 and data["net"]>0:data["admission_score"]=max(.46,self.base_admission-.03)

        if len(xs)>=10 and wins and losses:
            mfe=[_f(t.get("mfe")) for t in wins if t.get("mfe") is not None]
            mae=[abs(_f(t.get("mae"))) for t in losses if t.get("mae") is not None]
            holds=[_f(t.get("closed_unix"))-_f(t.get("opened_unix")) for t in wins if t.get("closed_unix")]
            if mfe:data["take_profit"]=max(.08,min(.22,_median(mfe,self.pump_tp)*.70))
            if mae:data["stop_loss"]=max(.045,min(.10,_median(mae,self.pump_stop)*.80))
            if holds:data["max_hold_seconds"]=max(30,min(120,_median(holds,self.pump_max_hold)*1.5))
        _atomic_json(self.pump_learning_path,data)
        return data

    def _adaptive_score(self,s,L):
        score=_f(s.get("base_score") or s.get("score"))
        fs=L.get("feature_stats") or {}
        for feat in L.get("promoted") or []:
            st=fs.get(feat) or {};wm=_f(st.get("win_mean"));lm=_f(st.get("loss_mean"));v=_f(s.get(feat))
            higher=feat not in ("largest_buyer_share","sell_ratio8","birth_age_seconds")
            if (higher and v>=wm) or ((not higher) and v<=wm):score+=.025
            elif (higher and v<=lm) or ((not higher) and v>=lm):score-=.02
        for feat in L.get("demoted") or []:
            st=fs.get(feat) or {};lm=_f(st.get("loss_mean"));v=_f(s.get(feat))
            higher=feat not in ("largest_buyer_share","sell_ratio8","birth_age_seconds")
            if (higher and v>=lm) or ((not higher) and v<=lm):score-=.015
        return max(0.0,min(1.0,score))

    def _enter_pump(self,s):
        half=self.pump_friction/2;entry=_f(s["price"])*(1+half)
        p={"position_id":f'PUMP-BP-{int(_now()*1000)}',"mode":"PAPER","status":"OPEN",
           "strategy":TARGET,"market":s["market"],"token":s["token"],"family":s["family"],
           "opened_unix":_now(),"reference_entry_price":s["price"],"entry_price":entry,
           "high_water_price":entry,"low_water_price":entry,"notional_usdc":self.pump_notional,
           "qty":self.pump_notional/entry,"modeled_entry_friction_usdc":self.pump_notional*half,
           "signal":dict(s)}
        self.pump_positions["positions"].append(p);_atomic_json(self.pump_positions_path,self.pump_positions);return p

    def _update_wallet_learning(self,trade):
        win=_f(trade.get("net_pnl_usdc"))>0;net=_f(trade.get("net_pnl_usdc"))
        for w in (trade.get("signal") or {}).get("early_buyers") or []:
            d=self.wallet_learning.setdefault("wallets",{}).setdefault(w,{"trades":0,"wins":0,"losses":0,"net":0.0})
            d["trades"]+=1;d["wins"]+=1 if win else 0;d["losses"]+=0 if win else 1;d["net"]+=net
        _atomic_json(self.pump_wallet_path,self.wallet_learning)

    def _manage_pump(self,latest_price,L):
        closed=[];half=self.pump_friction/2
        stop=_f(L.get("stop_loss"),self.pump_stop);tp=_f(L.get("take_profit"),self.pump_tp)
        trail=_f(L.get("trailing_stop"),self.pump_trail);max_hold=_f(L.get("max_hold_seconds"),self.pump_max_hold)
        for p in self.pump_positions["positions"]:
            if p.get("status")!="OPEN":continue
            px=_f(latest_price.get((p["market"],p["token"])))
            if px<=0:continue
            entry=_f(p["entry_price"]);p["high_water_price"]=max(_f(p.get("high_water_price"),entry),px)
            p["low_water_price"]=min(_f(p.get("low_water_price"),entry),px)
            ret=px/entry-1;tr=px/p["high_water_price"]-1;age=_now()-_f(p["opened_unix"]);reason=None
            if ret<=-stop:reason="STOP_LOSS"
            elif ret>=tp:reason="TAKE_PROFIT"
            elif p["high_water_price"]>=entry*1.06 and tr<=-trail:reason="TRAILING_STOP"
            elif age>=max_hold:reason="MAX_HOLD"
            if not reason:continue
            exit_px=px*(1-half);gross=p["qty"]*px-self.pump_notional;net=p["qty"]*exit_px-self.pump_notional
            p.update(status="CLOSED",closed_unix=_now(),reference_exit_price=px,exit_price=exit_px,
                     exit_reason=reason,gross_pnl_usdc=gross,
                     modeled_friction_usdc=gross-net+_f(p.get("modeled_entry_friction_usdc")),
                     net_pnl_usdc=net,net_return=net/self.pump_notional,
                     mfe=p["high_water_price"]/entry-1,mae=p["low_water_price"]/entry-1)
            self.pump_ledger["trades"].append(dict(p));closed.append(dict(p));self._update_wallet_learning(p)
        _atomic_json(self.pump_positions_path,self.pump_positions);_atomic_json(self.pump_ledger_path,self.pump_ledger)
        return closed

    def _coverage(self,rows,source_counts,birth_count,burst_family_counts):
        now=_now();fresh=[r for r in rows if abs(now-r["t"])<=self.source_fresh]
        fc=Counter(r["family"] for r in fresh)
        uniq_tokens=len({r["token"] for r in fresh});uniq_traders=len({r["trader"] for r in fresh if r["trader"]})
        context={rel:(self.physical_root/rel).is_file() for rel in CONTEXT_PATHS}
        gmgn=(self.physical_root/"qseries_v2/oracle_adapters/independent/oad_299_gmgn_solana_trader_intelligence.py").is_file()
        security=(self.physical_root/"qseries_v2/oracle_adapters/independent/oad_305_solana_launch_security_profile.py").is_file()
        pump_burst=sum(int(v or 0) for k,v in (burst_family_counts or {}).items() if "PUMP" in str(k).upper())
        connected=len(fresh)>0
        disconnect=bool(pump_burst>0 and not connected)
        return {"fresh_exact_trades":len(fresh),"pumpfun_fresh":fc["PUMP_FUN"],"pumpswap_fresh":fc["PUMP_SWAP"],
                "unique_tokens":uniq_tokens,"unique_traders":uniq_traders,"birth_rows":birth_count,
                "context_sources":sum(context.values()),"gmgn_module_available":gmgn,"security_module_available":security,
                "pump_burst_events":pump_burst,"source_connected":connected,"source_disconnect":disconnect,
                "source_files_with_rows":len(source_counts)}

    def cycle(self,progress=False,burst_family_counts=None):
        rows,files=ingest(self.root,self.cfg,progress=progress);hist=_histories(rows);latest={m:h[-1] for m,h in hist.items() if h}
        closed=self._manage(latest)

        eco_rows,source_counts=self._ecosystem_rows()
        births,creators,birth_count=self._birth_map()
        coverage=self._coverage(eco_rows,source_counts,birth_count,burst_family_counts)

        latest_pump={}
        for r in eco_rows:latest_pump[(r["market"],r["token"])]=r["price"]

        L=self._learning()
        pump_closed=self._manage_pump(latest_pump,L)
        L=self._learning()
        pump_ready=self._exact_signals(eco_rows,births,creators)

        dedup={}
        for s in pump_ready:
            k=(s["market"],s["token"])
            if k not in dedup or _f(s["score"])>_f(dedup[k]["score"]):dedup[k]=s
        pump_ready=list(dedup.values())
        for s in pump_ready:s["adaptive_score"]=self._adaptive_score(s,L)
        pump_ready.sort(key=lambda x:_f(x["adaptive_score"]),reverse=True)

        pump_tokens=Counter(p.get("token") for p in self._pump_open() if p.get("token"));pump_entered=[]
        for s in pump_ready:
            if len(self._pump_open())>=self.max_pump_open:break
            token=s.get("token")
            if token and pump_tokens[token]>=1:continue
            if token and self._pump_recent(token):continue
            if _f(s["adaptive_score"])<_f(L["admission_score"],self.base_admission):continue
            pump_entered.append(self._enter_pump(s))
            if token:pump_tokens[token]+=1

        stats=self.stats();champions=self.champions(stats)
        ready=[];reasons=Counter()
        for _,h in hist.items():
            for name in STRATEGIES:
                if name==TARGET:continue
                sig,reason=detect(name,h,self.cfg);reasons[f"{name}:{reason}"]+=1
                if sig and reason=="READY":ready.append(sig)
        ready.sort(key=lambda x:x["score"],reverse=True)

        open_now=self._open();token_counts=Counter(p.get("token") for p in open_now if p.get("token"))
        champion_open=sum(1 for p in open_now if p.get("strategy") in champions);challenger_open=len(open_now)-champion_open
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
            s=dict(s);s["selection_lane"]=lane;entered.append(self._enter(s))
            if lane=="CHAMPION":champion_entries+=1
            else:challenger_entries+=1
            if token:token_counts[token]+=1

        stats=self.stats();pstats=stats[TARGET];L=self._learning()
        pump_status={"source_mode":"JOINED_EXACT_PUMP_ECOSYSTEM","ready":len(pump_ready),"entered":len(pump_entered),
                     "closed_this_cycle":len(pump_closed),"open":len(self._pump_open()),"closed":pstats["closed"],
                     "wins":pstats["wins"],"losses":pstats["losses"],"win_rate":pstats["win_rate"],"net":pstats["net"],
                     "milestone":pstats["wins"]>=10 and pstats["net"]>0,"learning":L,"coverage":coverage,
                     "max_open":self.max_pump_open}
        _atomic_json(self.pump_status_path,pump_status)

        trades=self.ledger["trades"];ranked=sorted(({"strategy":k,**v} for k,v in stats.items()),key=lambda x:(x["net"],x["closed"]),reverse=True)
        status={"revision":REVISION,"strategy_count":len(STRATEGIES),"source_rows":len(rows),"markets_watched":len(hist),
                "tokens_watched":len({r.token for r in rows if r.token}),"champions":sorted(self.champions(stats)),
                "ready_signals":len(ready),"entered_this_cycle":len(entered),"champion_entries":champion_entries,
                "challenger_entries":challenger_entries,"closed_this_cycle":len(closed),"open_positions":len(self._open()),
                "closed_trades":len(trades),"arena_net_pnl_usdc":sum(_f(t.get("net_pnl_usdc")) for t in trades),
                "leaderboard":ranked,"pump_buy_pressure":pump_status,"paper_only":True,"real_money_moved":False}
        _atomic_json(self.status_path,status);return status
