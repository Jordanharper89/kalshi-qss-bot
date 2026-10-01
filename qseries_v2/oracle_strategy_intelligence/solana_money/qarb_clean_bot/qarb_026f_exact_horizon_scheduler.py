from __future__ import annotations
import asyncio,json,os,time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026b_forward_horizon_paper_pnl as base

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
TICK_SECONDS=0.05
_WARNED_AT=0.0

def safe_persist(book):
    global _WARNED_AT
    path=book.root/base.STATE_REL
    path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(book.summary(),sort_keys=True,indent=2)
    tmp=path.with_name(path.name+".%d.%d.tmp"%(os.getpid(),time.time_ns()))
    try:
        tmp.write_text(text,encoding="utf-8")
        for i in range(5):
            try:
                os.replace(tmp,path)
                return True
            except PermissionError:
                time.sleep(.05*(i+1))
        try:
            path.write_text(text,encoding="utf-8")
            return True
        except PermissionError:
            now=time.monotonic()
            if now-_WARNED_AT>15:
                print("[PAPER_STATE_WARN] scoreboard write blocked; runtime continues",flush=True)
                _WARNED_AT=now
            return False
    finally:
        try: tmp.unlink(missing_ok=True)
        except Exception: pass

def _patched_persist(self):
    safe_persist(self)

base.Book.persist=_patched_persist

class PaperSimulationLane:
    def __init__(self,root,state):
        self.root=Path(root)
        self.state=state
        self.book=base.Book(root,state["landing"])
        self.pairs={x.token:x for x in state.get("pairs",())}
        self.entries=0
        self.unsupported=0

        # Compatibility attributes read by the untouched persistent_profit_runtime.serve().
        self.attempts=0
        self.profitable=0
        self.best=None
        self.failures=0
        self.drops=0

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

        d={"direction":direction,"size_sol":float(r["size_sol"]),
           "net_sol":float(r["net_sol"]),"net_bps":float(r["net_bps"])}
        pos=self.book.enter(pair,d,time.monotonic())
        if pos is not None:
            self.entries+=1
            print("[PAPER_ENTRY] token=%s buy=%s sell=%s size=%.6f quote=%+.9f SOL bps=%+.2f slot=%d"%(
                pos.token[:10],buy,sell,pos.size_sol,pos.entry_quote_net_sol,
                pos.entry_quote_bps,pos.entry_slot),flush=True)

    def mark_due(self):
        now=time.monotonic()
        for pair in self.state.get("pairs",()):
            for row in self.book.update_pair(pair,now):
                print("[PAPER_EXIT] token=%s dir=%s size=%.6f horizon=%gs age=%.3fs lateness=%+.3fs pnl=%+.9f SOL"%(
                    row["token"][:10],row["direction"],row["size_sol"],
                    row["horizon_seconds"],row["actual_age_seconds"],
                    row["actual_age_seconds"]-row["horizon_seconds"],
                    row["paper_net_sol"]),flush=True)

    async def worker(self,stop):
        # This replaces only the old simulation worker. The original market runtime remains untouched.
        last_score=time.monotonic()
        while not stop.is_set():
            self.mark_due()
            now=time.monotonic()
            if now-last_score>=p.HEARTBEAT_SECONDS:
                print("[PAPER_SCORE] "+base._score_line(self.book)+
                      " open=%d entries=%d submitted=%d unsupported=%d"%(
                      len(self.book.open),self.entries,self.attempts,self.unsupported),flush=True)
                last_score=now
            try:
                await asyncio.wait_for(stop.wait(),timeout=TICK_SECONDS)
            except asyncio.TimeoutError:
                pass
        self.book.persist()

def install_lane():
    p.SimulationLane=PaperSimulationLane
    return p

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=None)
    a=ap.parse_args(argv)
    runtime=install_lane()
    print("[QARB-026F] UNTOUCHED 022D RUNTIME + PAPER LANE",flush=True)
    print("[ENGINE] persistent_profit_runtime.serve unchanged",flush=True)
    print("[HOOK] SimulationLane class only -> PaperSimulationLane",flush=True)
    print("[CLOCK] 50ms exact-horizon scheduler",flush=True)
    print("[STATE] Windows-safe persistence",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(runtime.serve(Path.cwd(),a.seconds))

if __name__=="__main__":
    main()
