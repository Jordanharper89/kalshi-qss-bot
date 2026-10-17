from __future__ import annotations
import asyncio
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061b_two_ws_valves_paper_lane as wv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061c_existing_runner_six_dex_valve_cutover as q61c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_SUBSCRIPTIONS_PER_CONNECTION=32
CONNECTION_STAGGER_SECONDS=1.25
SUB_DELAY_MS=90
RECONNECT_MIN_SECONDS=2.0
RECONNECT_MAX_SECONDS=30.0

_ORIG_WORKER=wv.q60b.p._worker

def capped_valves(addrs):
    a=list(dict.fromkeys(addrs))
    n=MAX_SUBSCRIPTIONS_PER_CONNECTION
    return [a[i:i+n] for i in range(0,len(a),n)]

async def staggered_worker(index,addresses,q,c,stop):
    if index:
        await asyncio.sleep(index*CONNECTION_STAGGER_SECONDS)
    return await _ORIG_WORKER(index,addresses,q,c,stop)

def install():
    p=wv.q60b.p
    m=wv.q60b.m
    p.RECONNECT_MIN=RECONNECT_MIN_SECONDS
    p.RECONNECT_MAX=RECONNECT_MAX_SECONDS
    m.STAGGER_SECONDS=0.0
    if hasattr(m,"SUB_DELAY_MS"):
        m.SUB_DELAY_MS=max(int(m.SUB_DELAY_MS),SUB_DELAY_MS)
    wv.two_valves=capped_valves
    m._shards=capped_valves
    p.m._shards=capped_valves
    p._worker=staggered_worker
    return q61c

def main(argv=None):
    runtime=install()
    print("[QARB-061D] STABLE SUBSCRIPTION VALVES",flush=True)
    print("[WS_CAP] max_accounts_per_connection=%d"%MAX_SUBSCRIPTIONS_PER_CONNECTION,flush=True)
    print("[WS_START] stagger_seconds=%.2f sub_delay_ms=%d"%(CONNECTION_STAGGER_SECONDS,SUB_DELAY_MS),flush=True)
    print("[WS_RECONNECT] min=%.1f max=%.1f"%(RECONNECT_MIN_SECONDS,RECONNECT_MAX_SECONDS),flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return runtime.main(argv)

if __name__=="__main__":
    main()
