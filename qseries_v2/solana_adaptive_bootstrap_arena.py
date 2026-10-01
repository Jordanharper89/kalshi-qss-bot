from __future__ import annotations
import json, os, time
from collections import Counter
from pathlib import Path

from qseries_v2.solana_24_strategy_arena import Arena, STRATEGIES, detect
from qseries_v2.solana_money_runner import _histories, ingest, _atomic_json

REVISION="QSB-012B-ADAPTIVE-BOOTSTRAP-V1"

class AdaptiveBootstrapArena(Arena):
    def __init__(self,root:Path):
        super().__init__(root,state_rel=Path("runtime_state/qseries/solana_24_strategy_arena"))
        self.min_closed=int(os.getenv("QSB012B_MIN_CLOSED","4"))
        self.min_win=float(os.getenv("QSB012B_MIN_WIN_RATE","0.55"))
        self.bootstrap_score=float(os.getenv("QSB012B_BOOTSTRAP_SCORE","0.60"))
        self.bootstrap_max_open=int(os.getenv("QSB012B_BOOTSTRAP_MAX_OPEN","8"))
        self.max_token_positions=int(os.getenv("QSB012B_MAX_OPEN_PER_TOKEN","1"))

    def stats(self):
        out={}
        for name in STRATEGIES:
            xs=[t for t in self.ledger["trades"] if t.get("strategy")==name]
            wins=sum(float(t.get("net_pnl_usdc") or 0)>0 for t in xs)
            net=sum(float(t.get("net_pnl_usdc") or 0) for t in xs)
            out[name]={"closed":len(xs),"wins":wins,"losses":len(xs)-wins,
                       "win_rate":wins/len(xs) if xs else None,
                       "net":net,"avg":net/len(xs) if xs else None}
        return out

    def promoted(self,stats):
        return {n for n,s in stats.items()
                if s["closed"]>=self.min_closed and s["net"]>0
                and (s["win_rate"] or 0)>=self.min_win and (s["avg"] or 0)>0}

    def cycle(self,progress=False):
        rows,files=ingest(self.root,self.cfg,progress=progress)
        hist=_histories(rows);latest={m:h[-1] for m,h in hist.items() if h}
        closed=self._manage(latest)

        stats=self.stats();promoted=self.promoted(stats)
        ready=[];reasons=Counter()
        for _,h in hist.items():
            for name in STRATEGIES:
                sig,reason=detect(name,h,self.cfg)
                reasons[f"{name}:{reason}"]+=1
                if sig and reason=="READY":
                    ready.append(sig)
        ready.sort(key=lambda x:x["score"],reverse=True)

        open_now=self._open()
        token_counts=Counter(p.get("token") for p in open_now if p.get("token"))
        strategy_counts=Counter(p.get("strategy") for p in open_now)
        entered=[]

        bootstrap = len(promoted)==0
        for s in ready:
            name=s["strategy"];token=s.get("token")
            if token and token_counts[token]>=self.max_token_positions:
                continue
            if self._recent(name,s["market"]):
                continue

            if bootstrap:
                # Critical deadlock repair: allow controlled paper exploration until evidence exists.
                if len(open_now)+len(entered)>=self.bootstrap_max_open:
                    break
                if strategy_counts[name]>=1:
                    continue
                if float(s.get("score") or 0)<self.bootstrap_score:
                    continue
            else:
                if name not in promoted:
                    continue
                if strategy_counts[name]>=2:
                    continue

            entered.append(self._enter(s))
            strategy_counts[name]+=1
            if token:token_counts[token]+=1

        trades=self.ledger["trades"];stats=self.stats();promoted=self.promoted(stats)
        ranked=sorted(({"strategy":k,**v} for k,v in stats.items()),
                      key=lambda x:(x["net"],x["closed"]),reverse=True)
        status={"revision":REVISION,"strategy_count":len(STRATEGIES),
                "source_rows":len(rows),"markets_watched":len(hist),
                "tokens_watched":len({r.token for r in rows if r.token}),
                "bootstrap_mode":len(promoted)==0,"promoted":sorted(promoted),
                "ready_signals":len(ready),"entered_this_cycle":len(entered),
                "closed_this_cycle":len(closed),"open_positions":len(self._open()),
                "closed_trades":len(trades),
                "arena_net_pnl_usdc":sum(float(t.get("net_pnl_usdc") or 0) for t in trades),
                "leaderboard":ranked,"why_no_trade":dict(reasons.most_common(30)),
                "paper_only":True,"real_money_moved":False}
        _atomic_json(self.status_path,status)
        return status
