from __future__ import annotations
import asyncio,os,time
from pathlib import Path
from time import perf_counter_ns

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026g_token_freshness_profit_audit as qg

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_CROSS_VENUE_AGE_MS=float(os.getenv("QARB_MAX_CROSS_VENUE_AGE_MS","750"))

class FreshOnlyPaperLane(qg.FreshnessPaperLane):
    def __init__(self,root,state):
        super().__init__(root,state)
        self.fresh_admitted=0
        self.rejected_unknown=0
        self.rejected_stale=0

    def submit(self,r):
        self.attempts+=1
        buy=r.get("buy_venue");sell=r.get("sell_venue")
        if buy=="PUMPSWAP" and sell=="METEORA_DLMM":
            direction="PUMP_TO_METEORA"
        elif buy=="METEORA_DLMM" and sell=="PUMPSWAP":
            direction="METEORA_TO_PUMP"
        else:
            self.unsupported+=1
            return

        pair=self.pairs.get(r.get("token"))
        if pair is None:
            self.unsupported+=1
            return

        pa,da,skew,ps,ds=self._freshness(pair)
        if pa is None or da is None:
            self.rejected_unknown+=1
            print("[FRESH_REJECT] token=%s reason=VENUE_NOT_YET_OBSERVED pump_age=%s dlmm_age=%s"%(
                r["token"][:10],"UNKNOWN" if pa is None else "%.1fms"%pa,
                "UNKNOWN" if da is None else "%.1fms"%da),flush=True)
            return

        if pa>MAX_CROSS_VENUE_AGE_MS or da>MAX_CROSS_VENUE_AGE_MS:
            self.rejected_stale+=1
            print("[FRESH_REJECT] token=%s reason=STALE_SIDE pump_age=%.1fms dlmm_age=%.1fms skew=%.1fms limit=%.0fms"%(
                r["token"][:10],pa,da,skew,MAX_CROSS_VENUE_AGE_MS),flush=True)
            return

        d={"direction":direction,"size_sol":float(r["size_sol"]),
           "net_sol":float(r["net_sol"]),"net_bps":float(r["net_bps"])}
        pos=self.book.enter(pair,d,time.monotonic())
        if pos is None:
            return

        self.entries+=1
        self.fresh_entries+=1
        self.fresh_admitted+=1
        print("[PAPER_ENTRY_FRESH] token=%s buy=%s sell=%s size=%.6f quote=%+.9f SOL bps=%+.2f slot=%d"%(
            pos.token[:10],buy,sell,pos.size_sol,pos.entry_quote_net_sol,
            pos.entry_quote_bps,pos.entry_slot),flush=True)
        print("[ENTRY_FRESHNESS] token=%s pump_age=%.1fms dlmm_age=%.1fms skew=%.1fms pump_slot=%d dlmm_slot=%d gate=PASS"%(
            pos.token[:10],pa,da,skew,ps,ds),flush=True)

    async def worker(self,stop):
        last_score=time.monotonic()
        while not stop.is_set():
            self.mark_due()
            now=time.monotonic()
            if now-last_score>=p.HEARTBEAT_SECONDS:
                print("[FRESH_GATE_SCORE] admitted=%d rejected_stale=%d rejected_unknown=%d submitted=%d open=%d"%(
                    self.fresh_admitted,self.rejected_stale,self.rejected_unknown,
                    self.attempts,len(self.book.open)),flush=True)
                print("[PAPER_SCORE_FRESH_ONLY] "+qg.base._score_line(self.book),flush=True)
                ranked=sorted(self.token_stats,key=lambda t:(
                    self.token_stats[t][2.0]["net_sol"]+
                    self.token_stats[t][5.0]["net_sol"]),reverse=True)
                for token in ranked[:8]:
                    print("[TOKEN_SCORE_FRESH_ONLY] token=%s %s"%(
                        token[:10],self._token_line(token)),flush=True)
                last_score=now
            try:
                await asyncio.wait_for(stop.wait(),timeout=qg.qf.TICK_SECONDS)
            except asyncio.TimeoutError:
                pass
        self.book.persist()

def install():
    qg.VENUE_TS.clear()
    p.m.pd.apply_account_event=qg.tracked_apply
    p.SimulationLane=FreshOnlyPaperLane
    return p

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=None)
    a=ap.parse_args(argv)
    runtime=install()
    print("[QARB-026H] FRESH CROSS-VENUE PAPER ADMISSION GATE",flush=True)
    print("[ENGINE] persistent_profit_runtime.serve unchanged",flush=True)
    print("[HOT_SIGNAL] unchanged; all qualified signals remain visible",flush=True)
    print("[PAPER_GATE] both PumpSwap and Meteora live-observed and <=%.0fms old"%MAX_CROSS_VENUE_AGE_MS,flush=True)
    print("[CLOCK] exact 2/5/15/30/60/90s scheduler retained",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(runtime.serve(Path.cwd(),a.seconds))

if __name__=="__main__":
    main()
