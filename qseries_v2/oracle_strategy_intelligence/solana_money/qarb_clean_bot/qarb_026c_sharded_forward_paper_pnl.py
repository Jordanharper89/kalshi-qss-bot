from __future__ import annotations
import asyncio,json,os,time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as live
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_026b_forward_horizon_paper_pnl import Book,HORIZONS,_score_line

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
SHARD_SIZE=int(os.getenv("QARB_PAPER_SHARD_SIZE","40"))
MAX_SECONDS=float(os.getenv("QARB_PAPER_RUNTIME_SECONDS","0"))

def shard_addresses(addresses,shard_size=SHARD_SIZE):
    n=max(1,int(shard_size))
    return [list(addresses[i:i+n]) for i in range(0,len(addresses),n)]

async def shard_reader(shard_id,addresses,queue,stop_event):
    import websockets
    while not stop_event.is_set():
        sub_to_addr={}
        try:
            async with websockets.connect(
                live.WS_URL,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000
            ) as ws:
                for i,a in enumerate(addresses,1):
                    req={"jsonrpc":"2.0","id":i,"method":"accountSubscribe",
                         "params":[a,{"encoding":"base64","commitment":"processed"}]}
                    await ws.send(json.dumps(req,separators=(",",":")))
                await queue.put(("SHARD_UP",shard_id,len(addresses)))
                while not stop_event.is_set():
                    raw=await ws.recv()
                    msg=json.loads(raw)
                    if "id" in msg and "result" in msg and isinstance(msg["result"],int):
                        rid=int(msg["id"])
                        if 1<=rid<=len(addresses):
                            sub_to_addr[int(msg["result"])]=addresses[rid-1]
                        continue
                    ev=live.parse_account_notification(msg,sub_to_addr)
                    if ev:
                        await queue.put(("EVENT",shard_id,ev))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await queue.put(("SHARD_DOWN",shard_id,f"{type(exc).__name__}:{exc}"))
            await asyncio.sleep(1.0)

async def serve(root,max_seconds=MAX_SECONDS):
    root=Path(root)
    pairs,landing=live.prepare_pairs(root)
    if not pairs:
        raise RuntimeError("NO_WARM_PAIRS")
    reg=live.account_registry(pairs)
    addresses=list(reg)
    shards=shard_addresses(addresses)
    book=Book(root,landing)
    queue=asyncio.Queue(maxsize=10000)
    stop_event=asyncio.Event()

    print("[QARB-026C] SHARDED FORWARD-HORIZON PAPER PNL",flush=True)
    print("[HORIZONS] "+",".join("%gs"%h for h in HORIZONS),flush=True)
    print("[TRANSPORT] accounts=%d shards=%d shard_size<=%d ws=%s"%(
        len(addresses),len(shards),SHARD_SIZE,live.WS_URL),flush=True)
    print("[EXIT] future websocket-updated pool state only; no instant realization",flush=True)
    print("[NO_SIM] transaction simulation/composer path absent",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)

    tasks=[asyncio.create_task(shard_reader(i+1,chunk,queue,stop_event))
           for i,chunk in enumerate(shards)]
    started=time.monotonic()
    last_score=started
    up=set()
    reconnects=0

    try:
        while True:
            now=time.monotonic()
            if max_seconds>0 and now-started>=max_seconds:
                break
            try:
                item=await asyncio.wait_for(queue.get(),timeout=1.0)
            except asyncio.TimeoutError:
                if time.monotonic()-last_score>=15:
                    print("[PAPER_SCORE] "+_score_line(book)+" open=%d shards_up=%d/%d reconnects=%d"%(
                        len(book.open),len(up),len(shards),reconnects),flush=True)
                    last_score=time.monotonic()
                continue

            kind=item[0]
            if kind=="SHARD_UP":
                _,sid,count=item
                up.add(sid)
                print("[WS_SHARD_UP] shard=%d accounts=%d active=%d/%d"%(sid,count,len(up),len(shards)),flush=True)
                continue
            if kind=="SHARD_DOWN":
                _,sid,reason=item
                up.discard(sid);reconnects+=1
                print("[WS_SHARD_RECONNECT] shard=%d reason=%s active=%d/%d"%(sid,reason,len(up),len(shards)),flush=True)
                continue

            _,sid,ev=item
            addr=ev["address"]
            if addr not in reg:
                continue
            idx,acct_kind=reg[addr]
            pair=pairs[idx]
            if not live.apply_account_event(pair,acct_kind,addr,ev["raw"],ev["slot"],ev["received_ns"]):
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
                print("[PAPER_SCORE] "+_score_line(book)+" open=%d shards_up=%d/%d reconnects=%d"%(
                    len(book.open),len(up),len(shards),reconnects),flush=True)
                last_score=time.monotonic()
    finally:
        stop_event.set()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        book.persist()

    print("[FINAL_PAPER_SCORE] "+json.dumps(book.summary(),sort_keys=True),flush=True)
    return book.summary()

def main():
    asyncio.run(serve(Path.cwd()))

if __name__=="__main__":
    main()
