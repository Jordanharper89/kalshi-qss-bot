from __future__ import annotations
import asyncio,json,time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_026b_forward_horizon_paper_pnl import Book,HORIZONS,_score_line

EXECUTION_AUTHORITY=False
PAPER_ONLY=True

class PaperLane:
    def __init__(self,root,state):
        self.root=Path(root)
        self.state=state
        self.book=Book(root,state["landing"])
        self.entries=0
        self.unsupported=0
        self.pairs_by_token={x.token:x for x in state.get("pairs",())}

    def submit(self,r):
        buy=r.get("buy_venue");sell=r.get("sell_venue")
        if buy=="PUMPSWAP" and sell=="METEORA_DLMM":
            direction="PUMP_TO_METEORA"
        elif buy=="METEORA_DLMM" and sell=="PUMPSWAP":
            direction="METEORA_TO_PUMP"
        else:
            self.unsupported+=1
            return None
        pair=self.pairs_by_token.get(r.get("token"))
        if pair is None:
            self.unsupported+=1
            return None
        d={"direction":direction,"size_sol":float(r["size_sol"]),
           "net_sol":float(r["net_sol"]),"net_bps":float(r["net_bps"])}
        pos=self.book.enter(pair,d,time.monotonic())
        if pos is not None:
            self.entries+=1
            print("[PAPER_ENTRY] token=%s buy=%s sell=%s size=%.6f quote=%+.9f SOL bps=%+.2f slot=%d"%(
                pos.token[:10],buy,sell,pos.size_sol,pos.entry_quote_net_sol,
                pos.entry_quote_bps,pos.entry_slot),flush=True)
        return pos

    def mark_event(self,ev):
        a=ev.get("address")
        if a not in self.state.get("preg",{}):
            return []
        i,_=self.state["preg"][a]
        pair=self.state["pairs"][i]
        rows=self.book.update_pair(pair,time.monotonic())
        for row in rows:
            print("[PAPER_EXIT] token=%s dir=%s size=%.6f horizon=%gs age=%.2fs pnl=%+.9f SOL"%(
                row["token"][:10],row["direction"],row["size_sol"],
                row["horizon_seconds"],row["actual_age_seconds"],row["paper_net_sol"]),flush=True)
        return rows

async def serve(root,max_seconds=None):
    root=Path(root)
    p.m.pd.MAX_PAIRS=p.MAX_PAIRS
    state=p.m.prepare(root)
    caps=p.m.capability(state)
    shards=p.m._shards(state["addresses"])
    c={"acks":0,"notifications":0,"priced_events":0,"observed_only_events":0,"signals":0,
       "event_errors":0,"queue_drops":0,"connections":0,"reconnects":0,
       "rate_limit_disconnects":0,"last_ws_error":None,"lat":[],"best":None}
    lane=PaperLane(root,state)

    print("[QARB-026D] NATIVE 022D FORWARD PAPER PNL",flush=True)
    print("[SOURCE] persistent_profit_runtime m.prepare/_shards/_worker/_process_event",flush=True)
    print("[HORIZONS] "+",".join("%gs"%h for h in HORIZONS),flush=True)
    print("[CAPABILITY] "+json.dumps(caps,sort_keys=True),flush=True)
    print("[LIVE] accounts=%d shards=%d priced_tokens=%d max_pairs=%d"%(
        len(state["addresses"]),len(shards),len(state["eps"]),p.MAX_PAIRS),flush=True)
    print("[SIM] disabled; qualified HOT_SIGNAL submit is redirected to PaperLane",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

    q=asyncio.Queue(maxsize=p.QUEUE_MAX)
    stop=asyncio.Event()
    p._initial_scan(state,c,lane)
    workers=[asyncio.create_task(p._worker(i,s,q,c,stop)) for i,s in enumerate(shards)]
    started=time.monotonic();last_hb=started;last_n=0
    try:
        while not stop.is_set():
            if p._STOP:break
            if max_seconds is not None and time.monotonic()-started>=float(max_seconds):break
            try:
                ev=await asyncio.wait_for(q.get(),timeout=.25)
                p._process_event(state,ev,c,lane)
                lane.mark_event(ev)
            except asyncio.TimeoutError:
                pass
            now=time.monotonic()
            if now-last_hb>=p.HEARTBEAT_SECONDS:
                span=max(.001,now-last_hb)
                eps=(c["notifications"]-last_n)/span
                print("[PAPER_SCORE] "+_score_line(lane.book)+
                      " open=%d entries=%d signals=%d notifications=%d eps=%.2f p99_ms=%s reconnects=%d rate_limits=%d unsupported=%d"%(
                      len(lane.book.open),lane.entries,c["signals"],c["notifications"],eps,
                      str(p._p99(c["lat"])),c["reconnects"],c["rate_limit_disconnects"],lane.unsupported),flush=True)
                last_hb=now;last_n=c["notifications"]
    finally:
        stop.set()
        for t in workers:t.cancel()
        await asyncio.gather(*workers,return_exceptions=True)
        lane.book.persist()

    result={"notifications":c["notifications"],"priced_events":c["priced_events"],
            "signals":c["signals"],"best":c["best"],"paper":lane.book.summary(),
            "paper_entries":lane.entries,"unsupported_routes":lane.unsupported,
            "reconnects":c["reconnects"],"rate_limit_disconnects":c["rate_limit_disconnects"],
            "p99_event_to_decision_ms":p._p99(c["lat"]),
            "execution_authority":False,"real_money_moved":False}
    print("[FINAL_PAPER_SCORE] "+json.dumps(result,sort_keys=True),flush=True)
    return result

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=None)
    a=ap.parse_args(argv)
    return asyncio.run(serve(Path.cwd(),a.seconds))

if __name__=="__main__":
    main()
