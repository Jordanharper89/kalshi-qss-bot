from __future__ import annotations
import asyncio,base64,json,os,struct,time
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns

from meteora_dlmm import PoolState
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

MAX_EVENT_TO_DECISION_MS=float(os.getenv("QARB_MAX_EVENT_TO_DECISION_MS","750"))
SIZES=tuple(float(x) for x in os.getenv("QARB_HOT_SIZES_SOL","0.005,0.01,0.025,0.05,0.1,0.18,0.28,0.5,0.9,1.1,1.4").split(",") if x.strip())
MAX_PAIRS=int(os.getenv("QARB_HOT_PAIRS","4"))
WS_URL=os.getenv("SOLANA_WS_URL","").strip() or (
    c.RPC.replace("https://","wss://",1).replace("http://","ws://",1)
)
PUMP_FEE_BPS=c.PUMP_FEE_BPS

@dataclass
class PairState:
    token:str
    pump_pool:str
    meteora_pool:str
    token_x:str
    token_y:str
    decimals_x:int
    decimals_y:int
    pump_base_vault:str
    pump_quote_vault:str
    pump_base_reserve:int
    pump_quote_reserve:int
    lb_bytes:bytes
    arrays:list
    dlmm_state:object
    last_slot:int=0
    last_event_ns:int=0

    def watched_accounts(self):
        return [self.pump_base_vault,self.pump_quote_vault,self.meteora_pool] + [a[1] for a in self.arrays]

def _token_amount_from_raw(raw):
    if len(raw)<72:
        raise RuntimeError("TOKEN_ACCOUNT_SHORT")
    return struct.unpack_from("<Q",raw,64)[0]

def _build_dlmm_state(pair):
    return PoolState.from_accounts(
        pair.lb_bytes,[x[2] for x in pair.arrays],
        decimals_x=pair.decimals_x,
        decimals_y=pair.decimals_y,
        lb_pair_key=c.b58d(pair.meteora_pool),
        exhaustive=True,
    )

def prepare_pairs(root):
    landing=engine.landing_cost_lamports()
    universe=engine.candidate_universe(root)
    out=[]
    for x in universe:
        if len(out)>=MAX_PAIRS:
            break
        try:
            meta=x.get("meteora_meta") or c.discover_dlmm(x["token"])
            pd,_=c.account(x["pump_pool"])
            pp=c.decode_pump_pool(pd)
            if pp["quote_mint"]!=c.WSOL:
                continue
            bd,_=c.account(pp["base_vault"])
            qd,_=c.account(pp["quote_vault"])
            lb,_=c.account(meta["address"])
            arrays=c.dlmm_arrays(meta["address"])
            ps=PairState(
                token=x["token"],pump_pool=x["pump_pool"],meteora_pool=meta["address"],
                token_x=meta["token_x"],token_y=meta["token_y"],
                decimals_x=int(meta["decimals_x"]),decimals_y=int(meta["decimals_y"]),
                pump_base_vault=pp["base_vault"],pump_quote_vault=pp["quote_vault"],
                pump_base_reserve=_token_amount_from_raw(bd),
                pump_quote_reserve=_token_amount_from_raw(qd),
                lb_bytes=lb,arrays=list(arrays),dlmm_state=None,
            )
            ps.dlmm_state=_build_dlmm_state(ps)
            out.append(ps)
        except Exception as exc:
            print("[WARM_SKIP] token=%s %s:%s"%(x["token"][:10],type(exc).__name__,exc),flush=True)
    return out,landing

def account_registry(pairs):
    reg={}
    for i,p in enumerate(pairs):
        reg[p.pump_base_vault]=(i,"PUMP_BASE")
        reg[p.pump_quote_vault]=(i,"PUMP_QUOTE")
        reg[p.meteora_pool]=(i,"DLMM_POOL")
        for j,a in enumerate(p.arrays):
            reg[a[1]]=(i,"DLMM_ARRAY_%d"%j)
    return reg

def subscription_requests(addresses):
    req=[]
    for i,a in enumerate(addresses,1):
        req.append({
            "jsonrpc":"2.0","id":i,"method":"accountSubscribe",
            "params":[a,{"encoding":"base64","commitment":"processed"}],
        })
    return req

def parse_account_notification(msg,sub_to_addr):
    if not isinstance(msg,dict) or msg.get("method")!="accountNotification":
        return None
    params=msg.get("params") or {}
    sub=params.get("subscription")
    addr=sub_to_addr.get(sub)
    if not addr:
        return None
    result=params.get("result") or {}
    ctx=result.get("context") or {}
    val=result.get("value") or {}
    data=val.get("data")
    if not data or not isinstance(data,list):
        return None
    return {
        "address":addr,
        "slot":int(ctx.get("slot") or 0),
        "raw":base64.b64decode(data[0]),
        "received_ns":perf_counter_ns(),
    }

def apply_account_event(pair,kind,address,raw,slot,received_ns):
    if kind=="PUMP_BASE":
        pair.pump_base_reserve=_token_amount_from_raw(raw)
    elif kind=="PUMP_QUOTE":
        pair.pump_quote_reserve=_token_amount_from_raw(raw)
    elif kind=="DLMM_POOL":
        pair.lb_bytes=raw
        pair.dlmm_state=_build_dlmm_state(pair)
    elif kind.startswith("DLMM_ARRAY_"):
        idx=int(kind.rsplit("_",1)[1])
        old=pair.arrays[idx]
        pair.arrays[idx]=(old[0],old[1],raw)
        pair.dlmm_state=_build_dlmm_state(pair)
    else:
        return False
    pair.last_slot=max(pair.last_slot,int(slot))
    pair.last_event_ns=int(received_ns)
    return True

def _pump_buy(pair,lamports):
    net=int(lamports)*(10000-PUMP_FEE_BPS)//10000
    return pair.pump_base_reserve*net//(pair.pump_quote_reserve+net)

def _pump_sell(pair,amount):
    net=int(amount)*(10000-PUMP_FEE_BPS)//10000
    return pair.pump_quote_reserve*net//(pair.pump_base_reserve+net)

def _dlmm_quote(pair,amount,input_mint):
    from meteora_dlmm import quote
    if input_mint==pair.token_x:
        swap_for_y=True
    elif input_mint==pair.token_y:
        swap_for_y=False
    else:
        raise RuntimeError("DLMM_DIRECTION")
    q=quote(pair.dlmm_state,amount_in=int(amount),swap_for_y=swap_for_y,strict=True)
    if not getattr(q,"complete",False) or int(getattr(q,"remaining_in",0) or 0):
        raise RuntimeError("DLMM_PARTIAL")
    return int(q.amount_out)

def best_local_route(pair,landing_lamports):
    best=None
    for size in SIZES:
        start=int(size*1e9)
        try:
            pb=_pump_buy(pair,start)
            mend=_dlmm_quote(pair,pb,pair.token)
            net1=mend-start-int(landing_lamports)
            bps1=net1/start*10000.0
            row1=("PUMP_TO_METEORA",size,mend,net1,bps1)

            mb=_dlmm_quote(pair,start,c.WSOL)
            pend=_pump_sell(pair,mb)
            net2=pend-start-int(landing_lamports)
            bps2=net2/start*10000.0
            row2=("METEORA_TO_PUMP",size,pend,net2,bps2)

            for row in (row1,row2):
                if best is None or row[3]>best[3]:
                    best=row
        except RuntimeError as exc:
            if str(exc)!="DLMM_PARTIAL":
                raise
    return best

def hot_event_decision(pair,landing_lamports,received_ns):
    t0=perf_counter_ns()
    row=best_local_route(pair,landing_lamports)
    decision_ns=perf_counter_ns()
    event_to_decision_ms=(decision_ns-int(received_ns))/1e6
    if row is None:
        return None
    direction,size,end_raw,net_raw,bps=row
    qualified=bool(
        event_to_decision_ms<=MAX_EVENT_TO_DECISION_MS and
        bps>=engine.MIN_NET_BPS
    )
    return {
        "token":pair.token,"pump_pool":pair.pump_pool,"meteora_pool":pair.meteora_pool,
        "direction":direction,"size_sol":size,"end_sol":end_raw/1e9,
        "net_sol":net_raw/1e9,"net_bps":bps,
        "event_to_decision_ms":event_to_decision_ms,
        "compute_us":(decision_ns-t0)/1e3,
        "slot":pair.last_slot,"qualified":qualified,
        "execution_authority":False,
    }

async def serve(root,max_seconds=15.0):
    import websockets
    pairs,landing=prepare_pairs(root)
    if not pairs:
        print("[LIVE] no warm crosslisted pairs",flush=True)
        return {"pairs":0,"notifications":0,"signals":0}
    reg=account_registry(pairs)
    addrs=list(reg)
    reqs=subscription_requests(addrs)
    print("[LIVE] ws=%s pairs=%d accounts=%d"%(WS_URL,len(pairs),len(addrs)),flush=True)

    notifications=0;signals=0
    sub_to_addr={}
    started=time.monotonic()

    async with websockets.connect(
        WS_URL,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000
    ) as ws:
        for req in reqs:
            await ws.send(json.dumps(req,separators=(",",":")))
        while time.monotonic()-started<float(max_seconds):
            timeout=max(0.05,min(1.0,float(max_seconds)-(time.monotonic()-started)))
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
            except asyncio.TimeoutError:
                continue
            msg=json.loads(raw)
            if "id" in msg and "result" in msg and isinstance(msg["result"],int):
                rid=int(msg["id"])
                if 1<=rid<=len(addrs):
                    sub_to_addr[int(msg["result"])]=addrs[rid-1]
                continue
            ev=parse_account_notification(msg,sub_to_addr)
            if not ev:
                continue
            notifications+=1
            idx,kind=reg[ev["address"]]
            pair=pairs[idx]
            if not apply_account_event(pair,kind,ev["address"],ev["raw"],ev["slot"],ev["received_ns"]):
                continue
            d=hot_event_decision(pair,landing,ev["received_ns"])
            if d and d["qualified"]:
                signals+=1
                print("[HOT_SIGNAL] token=%s dir=%s size=%.6f net=%+.9f SOL bps=%+.2f event_to_decision_ms=%.3f compute_us=%.2f slot=%d"%(
                    d["token"][:10],d["direction"],d["size_sol"],d["net_sol"],d["net_bps"],
                    d["event_to_decision_ms"],d["compute_us"],d["slot"]),flush=True)
    return {"pairs":len(pairs),"accounts":len(addrs),"notifications":notifications,"signals":signals}

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=15.0)
    a=ap.parse_args(argv)
    print("[QARB-005] LIVE ACCOUNT-SUBSCRIBE HOT PATH",flush=True)
    print("[CONTRACT] account event -> local quote decision <=750ms",flush=True)
    print("[HOT_PATH] no REST/RPC/filesystem after subscriptions are armed",flush=True)
    print("[INTERLEG] atomic execution target => logical gap 0ms",flush=True)
    print("[MODE] scanner/handoff only execution_authority=FALSE",flush=True)
    r=asyncio.run(serve(Path.cwd(),a.seconds))
    print("[RESULT] "+json.dumps(r,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
