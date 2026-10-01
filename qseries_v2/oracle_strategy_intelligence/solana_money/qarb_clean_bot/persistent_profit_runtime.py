from __future__ import annotations
import argparse,asyncio,json,os,signal,time
from pathlib import Path
from time import perf_counter_ns

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.live_atomic_simulation import SimulationLane

HEARTBEAT_SECONDS=float(os.getenv("QARB_HEARTBEAT_SECONDS","15"))
RECONNECT_MIN=float(os.getenv("QARB_WS_RECONNECT_MIN_SECONDS","1"))
RECONNECT_MAX=float(os.getenv("QARB_WS_RECONNECT_MAX_SECONDS","30"))
QUEUE_MAX=int(os.getenv("QARB_EVENT_QUEUE_MAX","20000"))
MAX_PAIRS=int(os.getenv("QARB_PERSISTENT_MAX_PAIRS","12"))
_STOP=False

def _stop(*_):
    global _STOP
    _STOP=True

def _p99(xs):
    if not xs:return None
    y=sorted(xs);return y[min(len(y)-1,int(len(y)*.99))]

def _best_text(best):
    if not best:return "None"
    return "%+.9f_SOL %+.2f_bps %s->%s"%(best["net_sol"],best["net_bps"],best["buy_venue"],best["sell_venue"])

def _process_event(state,ev,c,sim_lane):
    a=ev["address"];tokens=set();priced=False
    if a in state["preg"]:
        i,k=state["preg"][a];p=state["pairs"][i]
        try:
            if m.pd.apply_account_event(p,k,a,ev["raw"],ev["slot"],ev["received_ns"]):
                tokens.add(p.token);priced=True
        except Exception:c["event_errors"]+=1
    if a in state["creg"]:
        i,d=state["creg"][a];dd,st=state["cstates"][i]
        try:
            if m.rc.update(st,dd,a,ev["raw"],ev["received_ns"]):
                ep=m._cpmm_ep(dd,st)
                if ep:tokens.add(ep.token);priced=True
        except Exception:c["event_errors"]+=1
    if not priced:
        if a in state["observed"]:c["observed_only_events"]+=1
        return
    c["priced_events"]+=1
    for token in tokens:
        r=m.evaluate_token(token,state["eps"].get(token,()),state["landing"],ev["received_ns"])
        if not r:continue
        c["lat"].append(float(r["event_to_decision_ms"]))
        if c["best"] is None or r["net_sol"]>c["best"]["net_sol"]:c["best"]=r
        if r["qualified"]:
            c["signals"]+=1
            print("[HOT_SIGNAL] token=%s buy=%s sell=%s size=%.6f net=%+.9f SOL bps=%+.2f age_ms=%.3f"%(
                token[:10],r["buy_venue"],r["sell_venue"],r["size_sol"],r["net_sol"],r["net_bps"],r["event_to_decision_ms"]),flush=True)
            sim_lane.submit(r)

def _initial_scan(state,c,sim_lane):
    now=perf_counter_ns()
    for token,eps in state["eps"].items():
        r=m.evaluate_token(token,eps,state["landing"],now)
        if not r:continue
        if c["best"] is None or r["net_sol"]>c["best"]["net_sol"]:c["best"]=r
        if r["qualified"]:
            c["signals"]+=1
            print("[HOT_SIGNAL_INITIAL] token=%s buy=%s sell=%s size=%.6f net=%+.9f SOL bps=%+.2f"%(
                token[:10],r["buy_venue"],r["sell_venue"],r["size_sol"],r["net_sol"],r["net_bps"]),flush=True)
            sim_lane.submit(r)

async def _worker(index,addresses,q,c,stop):
    import websockets
    await asyncio.sleep(index*m.STAGGER_SECONDS)
    delay=RECONNECT_MIN
    while not stop.is_set():
        by_id={i+1:a for i,a in enumerate(addresses)};submap={}
        try:
            async with websockets.connect(m.WS_URL,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
                c["connections"]+=1
                for req in m._req(addresses):
                    if stop.is_set():break
                    await ws.send(json.dumps(req,separators=(",",":")))
                    if m.SUB_DELAY_MS>0:await asyncio.sleep(m.SUB_DELAY_MS/1000.0)
                delay=RECONNECT_MIN
                while not stop.is_set():
                    try:raw=await asyncio.wait_for(ws.recv(),timeout=1.0)
                    except asyncio.TimeoutError:continue
                    msg=json.loads(raw)
                    if "id" in msg and isinstance(msg.get("result"),int):
                        a=by_id.get(int(msg["id"]))
                        if a:submap[int(msg["result"])]=a;c["acks"]+=1
                        continue
                    ev=m._parse(msg,submap)
                    if not ev:continue
                    c["notifications"]+=1
                    try:q.put_nowait(ev)
                    except asyncio.QueueFull:c["queue_drops"]+=1
        except asyncio.CancelledError:raise
        except Exception as exc:
            txt=f"{type(exc).__name__}: {exc}";c["reconnects"]+=1;c["last_ws_error"]=txt
            low=txt.lower()
            if "1013" in low or "rate limit" in low or "too many subscriptions" in low:c["rate_limit_disconnects"]+=1
            print("[WS_RECOVER] shard=%d error=%s retry_in=%.1fs"%(index,txt,delay),flush=True)
            await asyncio.sleep(delay);delay=min(RECONNECT_MAX,max(RECONNECT_MIN,delay*2))

async def serve(root,max_seconds=None):
    root=Path(root);m.pd.MAX_PAIRS=MAX_PAIRS
    state=m.prepare(root);caps=m.capability(state);shards=m._shards(state["addresses"])
    c={"acks":0,"notifications":0,"priced_events":0,"observed_only_events":0,"signals":0,
       "event_errors":0,"queue_drops":0,"connections":0,"reconnects":0,
       "rate_limit_disconnects":0,"last_ws_error":None,"lat":[],"best":None}
    sim_lane=SimulationLane(root,state)
    print("[QARB-023] PERSISTENT LIVE ARBITRAGE + ATOMIC SIMULATION GATE",flush=True)
    print("[DISCOVERY] one startup hydration only",flush=True)
    print("[HOT] signal path remains in-memory; simulation runs on background lane",flush=True)
    print("[SIM] PumpSwap->Meteora DLMM qualified signals -> exact bound atomic simulateTransaction",flush=True)
    print("[CAPABILITY] "+json.dumps(caps,sort_keys=True),flush=True)
    print("[LIVE] accounts=%d shards=%d priced_tokens=%d max_pairs=%d"%(len(state["addresses"]),len(shards),len(state["eps"]),MAX_PAIRS),flush=True)
    print("[MODE] simulation gate only execution_authority=FALSE real_money_moved=FALSE",flush=True)

    q=asyncio.Queue(maxsize=QUEUE_MAX);stop=asyncio.Event()
    sim_task=asyncio.create_task(sim_lane.worker(stop))
    _initial_scan(state,c,sim_lane)
    workers=[asyncio.create_task(_worker(i,s,q,c,stop)) for i,s in enumerate(shards)]
    started=time.monotonic();last_hb=started;last_n=0
    try:
        while not stop.is_set():
            if _STOP:break
            if max_seconds is not None and time.monotonic()-started>=float(max_seconds):break
            try:ev=await asyncio.wait_for(q.get(),timeout=.25);_process_event(state,ev,c,sim_lane)
            except asyncio.TimeoutError:pass
            now=time.monotonic()
            if now-last_hb>=HEARTBEAT_SECONDS:
                span=max(.001,now-last_hb);eps=(c["notifications"]-last_n)/span
                sb=None if sim_lane.best is None else sim_lane.best.get("sim_pnl_sol")
                print("[HEARTBEAT] uptime_s=%d notifications=%d eps=%.2f priced_events=%d signals=%d best=%s p99_ms=%s sim_attempts=%d sim_profitable=%d sim_best=%s sim_failures=%d reconnects=%d rate_limits=%d"%(
                    int(now-started),c["notifications"],eps,c["priced_events"],c["signals"],_best_text(c["best"]),
                    str(_p99(c["lat"])),sim_lane.attempts,sim_lane.profitable,str(sb),sim_lane.failures,
                    c["reconnects"],c["rate_limit_disconnects"]),flush=True)
                last_hb=now;last_n=c["notifications"]
    finally:
        stop.set()
        for t in workers:t.cancel()
        sim_task.cancel()
        await asyncio.gather(*workers,sim_task,return_exceptions=True)

    return {"notifications":c["notifications"],"priced_events":c["priced_events"],"signals":c["signals"],
            "best":c["best"],"sim_attempts":sim_lane.attempts,"sim_profitable":sim_lane.profitable,
            "sim_best":sim_lane.best,"sim_failures":sim_lane.failures,"sim_drops":sim_lane.drops,
            "reconnects":c["reconnects"],"rate_limit_disconnects":c["rate_limit_disconnects"],
            "p99_event_to_decision_ms":_p99(c["lat"]),"execution_authority":False,"real_money_moved":False}

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=None,help="omit for continuous 24/7")
    a=ap.parse_args(argv)
    signal.signal(signal.SIGINT,_stop)
    if hasattr(signal,"SIGTERM"):signal.signal(signal.SIGTERM,_stop)
    r=asyncio.run(serve(Path.cwd(),a.seconds))
    print("[RESULT] "+json.dumps(r,sort_keys=True),flush=True);return r

if __name__=="__main__":main()
