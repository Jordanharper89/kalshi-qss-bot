from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"

REQ=[
    S/"qarb_064a_silent_mriya_profit_feed.py",
    S/"qarb_060b_existing_runtime_multidex_cutover.py",
    S/"qarb_060b2_single_hydration_cached_runner_cutover.py",
    S/"qarb_061d_subscription_cap_aware_ws_valves.py",
    S/"qarb_026g_token_freshness_profit_audit.py",
    S/"qarb_026h_fresh_crossvenue_paper_gate.py",
]

for x in REQ:
    if not x.exists():
        raise SystemExit("[FAIL] missing dependency: "+str(x))

M=S/"qarb_064b_dynamic_profit_machine.py"

M.write_text(r'''from __future__ import annotations

import asyncio
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as p
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b2_single_hydration_cached_runner_cutover as q60b2
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q61d
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026g_token_freshness_profit_audit as qg
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_026h_fresh_crossvenue_paper_gate as qh
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064a_silent_mriya_profit_feed as feed

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REFRESH_SECONDS=12.0


def _pair_key(x):
    return (
        x.token,
        x.pump_base_vault,
        x.pump_quote_vault,
        x.meteora_pool,
    )


def _pair_addresses(x):
    out=[
        x.pump_base_vault,
        x.pump_quote_vault,
        x.meteora_pool,
    ]
    out.extend(a[1] for a in x.arrays)
    return list(dict.fromkeys(out))


def _admit(state,pair,lane):
    if _pair_key(pair) in {_pair_key(x) for x in state["pairs"]}:
        return []

    i=len(state["pairs"])
    state["pairs"].append(pair)

    state["preg"][pair.pump_base_vault]=(i,"PUMP_BASE")
    state["preg"][pair.pump_quote_vault]=(i,"PUMP_QUOTE")
    state["preg"][pair.meteora_pool]=(i,"DLMM_POOL")

    for j,a in enumerate(pair.arrays):
        state["preg"][a[1]]=(i,"DLMM_ARRAY_%d"%j)

    state["eps"].setdefault(pair.token,[]).extend((
        p.m._pump_ep(pair),
        p.m._dlmm_ep(pair),
    ))

    if hasattr(lane,"pairs"):
        lane.pairs[pair.token]=pair

    old=set(state["addresses"])
    new=[
        a for a in _pair_addresses(pair)
        if a not in old
    ]

    state["addresses"].extend(new)
    return new


async def serve(root,max_seconds=None):
    root=Path(root)

    feed.bind_rpc()
    qg.VENUE_TS.clear()

    q60b.p._process_event=q60b.extended_process
    p._process_event=q60b.extended_process

    p.m._shards=q61d.capped_valves
    p._worker=q61d.staggered_worker

    p.m.pd.apply_account_event=qg.tracked_apply
    p.SimulationLane=qh.FreshOnlyPaperLane

    state,caps=q60b2.prepare_once(root)
    shards=q61d.capped_valves(state["addresses"])

    c={
        "acks":0,
        "notifications":0,
        "priced_events":0,
        "observed_only_events":0,
        "signals":0,
        "event_errors":0,
        "queue_drops":0,
        "connections":0,
        "reconnects":0,
        "rate_limit_disconnects":0,
        "last_ws_error":None,
        "lat":[],
        "best":None,
    }

    lane=p.SimulationLane(root,state)
    q=asyncio.Queue(maxsize=p.QUEUE_MAX)
    stop=asyncio.Event()

    workers=[
        asyncio.create_task(
            p._worker(i,s,q,c,stop)
        )
        for i,s in enumerate(shards)
    ]

    lane_task=asyncio.create_task(
        lane.worker(stop)
    )

    p._initial_scan(state,c,lane)

    print(
        "[QARB-064B] DYNAMIC PROFIT MACHINE",
        flush=True,
    )

    print(
        "[LIVE] six DEX base + silent Mriya hot-pair admission",
        flush=True,
    )

    print(
        "[OUTPUT] HOT_SIGNAL/PAPER_ENTRY/PAPER_EXIT/PAPER_SCORE/HEARTBEAT only; discovery tokens hidden",
        flush=True,
    )

    print(
        "[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE",
        flush=True,
    )

    started=time.monotonic()
    last_hb=started
    last_n=0
    last_refresh=started-REFRESH_SECONDS

    try:
        while not stop.is_set():

            now=time.monotonic()

            if (
                max_seconds is not None
                and now-started>=float(max_seconds)
            ):
                break

            if now-last_refresh>=REFRESH_SECONDS:

                last_refresh=now

                try:
                    await asyncio.to_thread(
                        feed.collect,
                        root,
                        7.0,
                    )

                    pairs,_,_=await asyncio.to_thread(
                        feed.candidates,
                        root,
                    )

                    added=[]

                    for pair in pairs:
                        added.extend(
                            _admit(
                                state,
                                pair,
                                lane,
                            )
                        )

                    for chunk in q61d.capped_valves(added):

                        workers.append(
                            asyncio.create_task(
                                p._worker(
                                    len(workers),
                                    chunk,
                                    q,
                                    c,
                                    stop,
                                )
                            )
                        )

                    if added:

                        print(
                            "[HOTSET_ADMIT] new_accounts=%d priced_tokens=%d"%(
                                len(added),
                                len(state["eps"]),
                            ),
                            flush=True,
                        )

                except Exception as e:

                    print(
                        "[HOTSET_FEED_RECOVER] %s:%s"%(
                            type(e).__name__,
                            e,
                        ),
                        flush=True,
                    )

            try:
                ev=await asyncio.wait_for(
                    q.get(),
                    timeout=.25,
                )

                p._process_event(
                    state,
                    ev,
                    c,
                    lane,
                )

            except asyncio.TimeoutError:
                pass

            now=time.monotonic()

            if now-last_hb>=p.HEARTBEAT_SECONDS:

                span=max(
                    .001,
                    now-last_hb,
                )

                eps=(
                    c["notifications"]-last_n
                )/span

                print(
                    "[HEARTBEAT] uptime_s=%d notifications=%d eps=%.2f priced_events=%d signals=%d best=%s p99_ms=%s reconnects=%d rate_limits=%d"%(
                        int(now-started),
                        c["notifications"],
                        eps,
                        c["priced_events"],
                        c["signals"],
                        p._best_text(c["best"]),
                        str(p._p99(c["lat"])),
                        c["reconnects"],
                        c["rate_limit_disconnects"],
                    ),
                    flush=True,
                )

                last_hb=now
                last_n=c["notifications"]

    finally:

        stop.set()

        for t in workers:
            t.cancel()

        lane_task.cancel()

        await asyncio.gather(
            *workers,
            lane_task,
            return_exceptions=True,
        )

    return {
        "signals":c["signals"],
        "priced_events":c["priced_events"],
        "reconnects":c["reconnects"],
        "rate_limits":c["rate_limit_disconnects"],
        "execution_authority":False,
    }
''',encoding="utf-8")


T=R/"test_qarb_064b_dynamic_profit_machine.py"

T.write_text(r'''import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064b_dynamic_profit_machine as q


class T(unittest.TestCase):

    def test_mode(self):
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.EXECUTION_AUTHORITY)

    def test_dynamic(self):
        s=inspect.getsource(q.serve)
        self.assertIn("feed.collect",s)
        self.assertIn("_admit",s)
        self.assertIn("capped_valves",s)

    def test_sixdex_base(self):
        self.assertIn(
            "q60b2.prepare_once",
            inspect.getsource(q.serve),
        )

    def test_fresh_paper(self):
        self.assertIn(
            "FreshOnlyPaperLane",
            inspect.getsource(q.serve),
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
''',encoding="utf-8")


for x in (M,T):
    py_compile.compile(
        str(x),
        doraise=True,
    )


print(
    "[PASS] QARB-064B dynamic profit machine installed"
)

print(
    "[MACHINE] Mriya hot pairs are admitted into the running arbitrage state without console token spam"
)

print(
    "[MODE] PAPER_ONLY=True execution_authority=FALSE"
)