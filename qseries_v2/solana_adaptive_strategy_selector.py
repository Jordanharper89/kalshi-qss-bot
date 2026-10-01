from __future__ import annotations
import json, os, time
from collections import Counter
from pathlib import Path

from qseries_v2.solana_24_strategy_arena import Arena, STRATEGIES, detect
from qseries_v2.solana_money_runner import _histories, ingest, _atomic_json

REVISION="QSB-011-ADAPTIVE-STRATEGY-SELECTION-V1"

class AdaptiveArena(Arena):
    def __init__(self,root:Path):
        super().__init__(root,state_rel=Path("runtime_state/qseries/solana_24_strategy_arena"))
        self.min_closed=int(os.getenv("QSB011_MIN_CLOSED","4"))
        self.min_win=float(os.getenv("QSB011_MIN_WIN_RATE","0.55"))
        self.max_token_positions=int(os.getenv("QSB011_MAX_OPEN_PER_TOKEN","1"))

    def _stats(self):
        out={}
        for name in STRATEGIES:
            xs=[t for t in self.ledger["trades"] if t.get("strategy")==name]
            wins=sum(float(t.get("net_pnl_usdc") or 0)>0 for t in xs)
            net=sum(float(t.get("net_pnl_usdc") or 0) for t in xs)
            out[name]={"closed":len(xs),"wins":wins,"losses":len(xs)-wins,
                       "win_rate":wins/len(xs) if xs else None,"net":net,
                       "avg":net/len(xs) if xs else None}
        return out

    def _eligible(self,name,stats):
        s=stats[name]
        if s["closed"]<self.min_closed:
            return False,"INSUFFICIENT_EVIDENCE"
        if s["net"]<=0:
            return False,"NEGATIVE_NET"
        if (s["win_rate"] or 0)<self.min_win:
            return False,"WIN_RATE_GATE"
        if (s["avg"] or 0)<=0:
            return False,"NEGATIVE_AVG"
        return True,"PROMOTED"

    def cycle(self,progress=False):
        rows,files=ingest(self.root,self.cfg,progress=progress)
        hist=_histories(rows);latest={m:h[-1] for m,h in hist.items() if h}
        closed=self._manage(latest)
        stats=self._stats()
        promoted={n for n in STRATEGIES if self._eligible(n,stats)[0]}
        quarantined={n:self._eligible(n,stats)[1] for n in STRATEGIES if n not in promoted}

        ready=[];reasons=Counter()
        for _,h in hist.items():
            for name in STRATEGIES:
                sig,reason=detect(name,h,self.cfg)
                reasons[f"{name}:{reason}"]+=1
                if sig and reason=="READY":
                    ready.append(sig)
        ready.sort(key=lambda s:s["score"],reverse=True)

        open_positions=self._open()
        token_counts=Counter(p.get("token") for p in open_positions if p.get("token"))
        entered=[]
        for s in ready:
            name=s["strategy"];token=s.get("token")
            if name not in promoted:
                reasons[f"{name}:BLOCKED_{quarantined.get(name,'NOT_PROMOTED')}"]+=1;continue
            if token and token_counts[token]>=self.max_token_positions:
                reasons[f"{name}:TOKEN_CONCENTRATION_BLOCK"]+=1;continue
            if self._recent(name,s["market"]):
                reasons[f"{name}:COOLDOWN"]+=1;continue
            entered.append(self._enter(s))
            if token:token_counts[token]+=1

        trades=self.ledger["trades"]
        stats=self._stats()
        ranked=sorted(({"strategy":k,**v} for k,v in stats.items()),
                      key=lambda x:(x["net"],x["closed"]),reverse=True)
        status={"revision":REVISION,"strategy_count":len(STRATEGIES),
                "source_rows":len(rows),"markets_watched":len(hist),
                "tokens_watched":len({r.token for r in rows if r.token}),
                "promoted":sorted(promoted),"quarantined":quarantined,
                "ready_signals":len(ready),"entered_this_cycle":len(entered),
                "closed_this_cycle":len(closed),"open_positions":len(self._open()),
                "closed_trades":len(trades),
                "arena_net_pnl_usdc":sum(float(t.get("net_pnl_usdc") or 0) for t in trades),
                "leaderboard":ranked,"why_no_trade":dict(reasons.most_common(30)),
                "paper_only":True,"real_money_moved":False}
        _atomic_json(self.status_path,status)
        return status
