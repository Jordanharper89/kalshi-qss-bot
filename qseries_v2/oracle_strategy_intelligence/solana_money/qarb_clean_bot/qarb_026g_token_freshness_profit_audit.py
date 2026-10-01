from __future__ import annotations
import asyncio,json,time
from collections import defaultdict
from pathlib import Path
from time import perf_counter_ns

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026f_exact_horizon_scheduler as qf
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026b_forward_horizon_paper_pnl as base

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
VENUE_TS={}
_ORIG_APPLY=p.m.pd.apply_account_event

def _venue(kind):
    if str(kind).startswith("PUMP_"): return "PUMPSWAP"
    if str(kind).startswith("DLMM_"): return "METEORA_DLMM"
    return None

def tracked_apply(pair,kind,address,raw,slot,received_ns):
    ok=_ORIG_APPLY(pair,kind,address,raw,slot,received_ns)
    if ok:
        v=_venue(kind)
        if v:
            x=VENUE_TS.setdefault(id(pair),{"PUMPSWAP":0,"METEORA_DLMM":0,
                                            "PUMP_SLOT":0,"DLMM_SLOT":0})
            x[v]=int(received_ns)
            if v=="PUMPSWAP": x["PUMP_SLOT"]=max(x["PUMP_SLOT"],int(slot))
            else: x["DLMM_SLOT"]=max(x["DLMM_SLOT"],int(slot))
    return ok

class FreshnessPaperLane(qf.PaperSimulationLane):
    def __init__(self,root,state):
        super().__init__(root,state)
        self.token_stats=defaultdict(lambda:defaultdict(lambda:{"trades":0,"wins":0,"net_sol":0.0}))
        self.fresh_entries=0
        self.one_side_unknown=0

    def _freshness(self,pair):
        now=perf_counter_ns()
        x=VENUE_TS.get(id(pair),{})
        pn=int(x.get("PUMPSWAP",0) or 0)
        dn=int(x.get("METEORA_DLMM",0) or 0)
        pa=None if not pn else max(0.0,(now-pn)/1e6)
        da=None if not dn else max(0.0,(now-dn)/1e6)
        skew=None if pa is None or da is None else abs(pa-da)
        return pa,da,skew,int(x.get("PUMP_SLOT",0) or 0),int(x.get("DLMM_SLOT",0) or 0)

    def submit(self,r):
        self.attempts+=1
        buy=r.get("buy_venue");sell=r.get("sell_venue")
        if buy=="PUMPSWAP" and sell=="METEORA_DLMM":
            direction="PUMP_TO_METEORA"
        elif buy=="METEORA_DLMM" and sell=="PUMPSWAP":
            direction="METEORA_TO_PUMP"
        else:
            self.unsupported+=1;return

        pair=self.pairs.get(r.get("token"))
        if pair is None:
            self.unsupported+=1;return

        d={"direction":direction,"size_sol":float(r["size_sol"]),
           "net_sol":float(r["net_sol"]),"net_bps":float(r["net_bps"])}
        pos=self.book.enter(pair,d,time.monotonic())
        if pos is None:return

        self.entries+=1
        pa,da,skew,ps,ds=self._freshness(pair)
        if pa is not None and da is not None:self.fresh_entries+=1
        else:self.one_side_unknown+=1
        def fmt(x): return "UNKNOWN" if x is None else "%.1fms"%x
        print("[PAPER_ENTRY] token=%s buy=%s sell=%s size=%.6f quote=%+.9f SOL bps=%+.2f slot=%d"%(
            pos.token[:10],buy,sell,pos.size_sol,pos.entry_quote_net_sol,pos.entry_quote_bps,pos.entry_slot),flush=True)
        print("[ENTRY_FRESHNESS] token=%s pump_age=%s dlmm_age=%s skew=%s pump_slot=%d dlmm_slot=%d"%(
            pos.token[:10],fmt(pa),fmt(da),fmt(skew),ps,ds),flush=True)

    def mark_due(self):
        now=time.monotonic()
        for pair in self.state.get("pairs",()):
            rows=self.book.update_pair(pair,now)
            for row in rows:
                h=float(row["horizon_seconds"]);net=float(row["paper_net_sol"])
                s=self.token_stats[row["token"]][h]
                s["trades"]+=1;s["wins"]+=int(net>0);s["net_sol"]+=net
                print("[PAPER_EXIT] token=%s dir=%s size=%.6f horizon=%gs age=%.3fs lateness=%+.3fs pnl=%+.9f SOL"%(
                    row["token"][:10],row["direction"],row["size_sol"],h,
                    row["actual_age_seconds"],row["actual_age_seconds"]-h,net),flush=True)

    def _token_line(self,token):
        parts=[]
        for h in base.HORIZONS:
            s=self.token_stats[token][float(h)]
            w=0 if not s["trades"] else 100*s["wins"]/s["trades"]
            parts.append("%gs:t=%d w=%.0f%% pnl=%+.6f"%(h,s["trades"],w,s["net_sol"]))
        return " | ".join(parts)

    async def worker(self,stop):
        last_score=time.monotonic()
        while not stop.is_set():
            self.mark_due()
            now=time.monotonic()
            if now-last_score>=p.HEARTBEAT_SECONDS:
                print("[PAPER_SCORE] "+base._score_line(self.book)+
                      " open=%d entries=%d submitted=%d unsupported=%d fresh_entries=%d freshness_unknown=%d"%(
                      len(self.book.open),self.entries,self.attempts,self.unsupported,
                      self.fresh_entries,self.one_side_unknown),flush=True)
                ranked=sorted(self.token_stats, key=lambda t:(
                    self.token_stats[t][2.0]["net_sol"]+self.token_stats[t][5.0]["net_sol"]),reverse=True)
                for token in ranked[:8]:
                    print("[TOKEN_SCORE] token=%s %s"%(token[:10],self._token_line(token)),flush=True)
                last_score=now
            try:
                await asyncio.wait_for(stop.wait(),timeout=qf.TICK_SECONDS)
            except asyncio.TimeoutError:
                pass
        self.book.persist()

def install():
    p.m.pd.apply_account_event=tracked_apply
    p.SimulationLane=FreshnessPaperLane
    return p

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=None)
    a=ap.parse_args(argv)
    runtime=install()
    print("[QARB-026G] TOKEN PROFIT + CROSS-VENUE FRESHNESS AUDIT",flush=True)
    print("[ENGINE] persistent_profit_runtime.serve unchanged",flush=True)
    print("[AUDIT] separate PumpSwap/Meteora event age + per-token horizon PNL",flush=True)
    print("[CLOCK] 50ms exact-horizon scheduler retained",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(runtime.serve(Path.cwd(),a.seconds))

if __name__=="__main__":
    main()
