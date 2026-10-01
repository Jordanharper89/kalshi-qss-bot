from __future__ import annotations
import asyncio,json,os,time
from dataclasses import dataclass,field
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as live

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
HORIZONS=tuple(float(x) for x in os.getenv("QARB_PAPER_HORIZONS","2,5,15,30,60,90").split(",") if x.strip())
EXTRA_FRICTION_BPS=float(os.getenv("QARB_PAPER_EXTRA_FRICTION_BPS","25"))
MAX_SECONDS=float(os.getenv("QARB_PAPER_RUNTIME_SECONDS","0"))
STATE_REL=Path("runtime_state/qseries/qarb_clean_bot/paper_forward_horizon_state.json")
TRADES_REL=Path("runtime_state/qseries/qarb_clean_bot/paper_forward_horizon_trades.jsonl")

@dataclass
class Position:
    token:str
    direction:str
    size_sol:float
    start_lamports:int
    token_qty:int
    entry_time:float
    entry_slot:int
    entry_quote_net_sol:float
    entry_quote_bps:float
    remaining:set=field(default_factory=set)

class Book:
    def __init__(self,root,landing_lamports):
        self.root=Path(root)
        self.landing=int(landing_lamports)
        self.open={}
        self.closed=[]
        self.by_h={h:{"trades":0,"wins":0,"losses":0,"net_sol":0.0,"peak_sol":0.0,"max_dd_sol":0.0} for h in HORIZONS}

    def key(self,token,direction,size):
        return (token,direction,round(float(size),9))

    def enter(self,pair,decision,now=None):
        now=time.monotonic() if now is None else float(now)
        direction=decision["direction"]
        size=float(decision["size_sol"])
        key=self.key(pair.token,direction,size)
        if key in self.open:
            return None
        start=int(size*1e9)
        if direction=="PUMP_TO_METEORA":
            qty=live._pump_buy(pair,start)
        elif direction=="METEORA_TO_PUMP":
            qty=live._dlmm_quote(pair,start,live.c.WSOL)
        else:
            return None
        p=Position(
            token=pair.token,direction=direction,size_sol=size,start_lamports=start,
            token_qty=int(qty),entry_time=now,entry_slot=int(pair.last_slot),
            entry_quote_net_sol=float(decision["net_sol"]),
            entry_quote_bps=float(decision["net_bps"]),
            remaining=set(HORIZONS),
        )
        self.open[key]=p
        return p

    def mark_out_lamports(self,pair,pos):
        if pos.direction=="PUMP_TO_METEORA":
            return int(live._dlmm_quote(pair,pos.token_qty,pair.token))
        if pos.direction=="METEORA_TO_PUMP":
            return int(live._pump_sell(pair,pos.token_qty))
        raise RuntimeError("UNKNOWN_DIRECTION")

    def update_pair(self,pair,now=None):
        now=time.monotonic() if now is None else float(now)
        rows=[]
        for key,pos in list(self.open.items()):
            if pos.token!=pair.token:
                continue
            age=now-pos.entry_time
            due=sorted(h for h in pos.remaining if age>=h)
            if not due:
                continue
            try:
                out=self.mark_out_lamports(pair,pos)
            except RuntimeError:
                continue
            friction=int(pos.start_lamports*(EXTRA_FRICTION_BPS/10000.0))
            net_lamports=out-pos.start_lamports-self.landing-friction
            net_sol=net_lamports/1e9
            for h in due:
                row={
                    "token":pos.token,"direction":pos.direction,"size_sol":pos.size_sol,
                    "horizon_seconds":h,"actual_age_seconds":age,
                    "entry_slot":pos.entry_slot,"exit_slot":int(pair.last_slot),
                    "entry_quote_net_sol":pos.entry_quote_net_sol,
                    "entry_quote_bps":pos.entry_quote_bps,
                    "token_qty":pos.token_qty,"exit_lamports":out,
                    "landing_lamports":self.landing,
                    "extra_friction_bps":EXTRA_FRICTION_BPS,
                    "paper_net_sol":net_sol,
                    "paper_only":True,"execution_authority":False,
                }
                self.record(h,row)
                rows.append(row)
                pos.remaining.remove(h)
            if not pos.remaining:
                del self.open[key]
        return rows

    def record(self,h,row):
        s=self.by_h[h]
        s["trades"]+=1
        if row["paper_net_sol"]>0:s["wins"]+=1
        else:s["losses"]+=1
        s["net_sol"]+=row["paper_net_sol"]
        s["peak_sol"]=max(s["peak_sol"],s["net_sol"])
        s["max_dd_sol"]=max(s["max_dd_sol"],s["peak_sol"]-s["net_sol"])
        self.closed.append(row)
        p=self.root/TRADES_REL;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("a",encoding="utf-8") as f:
            f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        self.persist()

    def summary(self):
        out={}
        for h,s in self.by_h.items():
            x=dict(s)
            x["win_rate"]=0.0 if not s["trades"] else s["wins"]/s["trades"]
            out[str(int(h) if float(h).is_integer() else h)]=x
        return {"horizons":out,"open_positions":len(self.open),
                "paper_only":True,"execution_authority":False,
                "extra_friction_bps":EXTRA_FRICTION_BPS}

    def persist(self):
        p=self.root/STATE_REL;p.parent.mkdir(parents=True,exist_ok=True)
        t=p.with_suffix(".tmp")
        t.write_text(json.dumps(self.summary(),sort_keys=True,indent=2),encoding="utf-8")
        t.replace(p)

def _score_line(book):
    parts=[]
    for h in HORIZONS:
        s=book.by_h[h]
        wr=0.0 if not s["trades"] else 100.0*s["wins"]/s["trades"]
        parts.append("%gs:t=%d w=%.0f%% pnl=%+.6f"%(h,s["trades"],wr,s["net_sol"]))
    return " | ".join(parts)

async def serve(root,max_seconds=MAX_SECONDS):
    import websockets
    root=Path(root)
    pairs,landing=live.prepare_pairs(root)
    if not pairs:
        raise RuntimeError("NO_WARM_PAIRS")
    reg=live.account_registry(pairs)
    addrs=list(reg)
    reqs=live.subscription_requests(addrs)
    book=Book(root,landing)
    pair_by_token={p.token:p for p in pairs}

    print("[QARB-026B] FORWARD-HORIZON PAPER PNL",flush=True)
    print("[HORIZONS] "+",".join("%gs"%h for h in HORIZONS),flush=True)
    print("[ENTRY] qualified HOT_SIGNAL only; one open position per token/route/size",flush=True)
    print("[EXIT] future websocket-updated pool state only; no instant realization",flush=True)
    print("[ACCOUNTING] buy-leg fee in live quote + sell-leg fee in live quote + landing + %.2f extra bps"%EXTRA_FRICTION_BPS,flush=True)
    print("[LIVE] pairs=%d accounts=%d ws=%s"%(len(pairs),len(addrs),live.WS_URL),flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

    sub_to_addr={}
    started=time.monotonic()
    last_score=started

    async with websockets.connect(live.WS_URL,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
        for req in reqs:
            await ws.send(json.dumps(req,separators=(",",":")))
        while True:
            now=time.monotonic()
            if max_seconds>0 and now-started>=max_seconds:
                break
            timeout=1.0
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
            except asyncio.TimeoutError:
                if time.monotonic()-last_score>=15:
                    print("[PAPER_SCORE] "+_score_line(book)+" open=%d"%len(book.open),flush=True)
                    last_score=time.monotonic()
                continue

            msg=json.loads(raw)
            if "id" in msg and "result" in msg and isinstance(msg["result"],int):
                rid=int(msg["id"])
                if 1<=rid<=len(addrs):
                    sub_to_addr[int(msg["result"])]=addrs[rid-1]
                continue

            ev=live.parse_account_notification(msg,sub_to_addr)
            if not ev:
                continue
            idx,kind=reg[ev["address"]]
            pair=pairs[idx]
            if not live.apply_account_event(pair,kind,ev["address"],ev["raw"],ev["slot"],ev["received_ns"]):
                continue

            now=time.monotonic()
            for row in book.update_pair(pair,now):
                print("[PAPER_EXIT] token=%s dir=%s size=%.6f horizon=%gs age=%.2fs pnl=%+.9f SOL"%(
                    row["token"][:10],row["direction"],row["size_sol"],row["horizon_seconds"],
                    row["actual_age_seconds"],row["paper_net_sol"]),flush=True)

            d=live.hot_event_decision(pair,landing,ev["received_ns"])
            if d and d["qualified"]:
                p=book.enter(pair,d,now)
                if p is not None:
                    print("[PAPER_ENTRY] token=%s dir=%s size=%.6f quote=%+.9f SOL bps=%+.2f slot=%d"%(
                        p.token[:10],p.direction,p.size_sol,p.entry_quote_net_sol,p.entry_quote_bps,p.entry_slot),flush=True)

            if time.monotonic()-last_score>=15:
                print("[PAPER_SCORE] "+_score_line(book)+" open=%d"%len(book.open),flush=True)
                last_score=time.monotonic()

    book.persist()
    print("[FINAL_PAPER_SCORE] "+json.dumps(book.summary(),sort_keys=True),flush=True)
    return book.summary()

def main():
    asyncio.run(serve(Path.cwd()))

if __name__=="__main__":
    main()
