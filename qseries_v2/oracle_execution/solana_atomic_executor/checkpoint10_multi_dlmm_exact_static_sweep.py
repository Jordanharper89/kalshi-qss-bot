from __future__ import annotations

import time
import urllib.error

from pathlib import Path

from meteora_dlmm import PoolState

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint9_multi_dlmm_pool_coverage_diagnostic as c9
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

MAX_POOLS_PER_TOKEN=8
PAIR_CAP=32
ACCOUNT_CAP=768

SIZES=(
    0.001,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    1.000,
    1.400,
)


def _with_429(label,fn):
    last=None

    for attempt in range(6):
        try:
            return fn()
        except urllib.error.HTTPError as exc:
            last=exc

            if getattr(exc,"code",None)!=429:
                raise

            delay=min(
                8.0,
                .50*(2**attempt),
            )

            print(
                "[CHECKPOINT10_429] "
                "%s attempt=%d sleep=%.2fs"
                %(label,attempt+1,delay),
                flush=True,
            )

            time.sleep(delay)

    raise last or RuntimeError(
        "CHECKPOINT10_RPC_RETRY_EXHAUSTED"
    )


def _hydrate_alt(meta):
    pool=str(meta["address"])

    lb,_=_with_429(
        "pool="+pool[:10],
        lambda:c.account(pool),
    )

    arrays=_with_429(
        "arrays="+pool[:10],
        lambda:c.dlmm_arrays(pool),
    )

    state=PoolState.from_accounts(
        lb,
        [x[2] for x in arrays],
        decimals_x=int(meta["decimals_x"]),
        decimals_y=int(meta["decimals_y"]),
        lb_pair_key=c.b58d(pool),
        exhaustive=True,
    )

    return state,list(arrays)


def _snapshot(pair,meta,state):
    return {
        "token":str(pair.token),
        "pump_pool":str(pair.pump_pool),
        "meteora":dict(meta),
        "dlmm_state":state,
        "pump_base_reserve":
            int(pair.pump_base_reserve),
        "pump_quote_reserve":
            int(pair.pump_quote_reserve),
    }


def _candidate_metas(token,selected_pool):
    rows=c9._all_ws_sol_pools(
        token
    )

    chosen=[]

    for row in rows[:MAX_POOLS_PER_TOKEN]:
        chosen.append(dict(row))

    selected=next(
        (
            dict(row)
            for row in rows
            if row["address"]==selected_pool
        ),
        None,
    )

    if (
        selected is not None
        and all(
            x["address"]!=selected_pool
            for x in chosen
        )
    ):
        chosen.append(selected)

    return chosen


def _best_for_pool(snap):
    best=None
    quote_count=0
    partial_count=0

    for size in SIZES:
        try:
            rows=r.q18.exact_snapshot_opportunities(
                snap,
                size,
            )
        except RuntimeError as exc:
            if str(exc)=="DLMM_PARTIAL":
                partial_count+=1
                continue
            raise

        for row in rows:
            quote_count+=1

            if (
                best is None
                or int(row["local_net"])
                >int(best["local_net"])
            ):
                best=dict(row)

    return best,quote_count,partial_count


def main():
    old_pair_cap=pd.MAX_PAIRS
    old_account_cap=m.MAX_ACCOUNTS

    pd.MAX_PAIRS=PAIR_CAP
    m.MAX_ACCOUNTS=ACCOUNT_CAP

    state=None

    try:
        state,_=r.q25.prepare_once(
            Path.cwd()
        )

        r.q25.bind_cached_state(
            state
        )

        r.install_proven_hot_math(
            state
        )

        pairs={
            str(pair.token):pair
            for pair in list(
                state.get("pairs")
                or []
            )
        }

        for pair in pairs.values():
            r.q18.worker().warm(
                str(pair.pump_pool)
            )

        print(
            "[CHECKPOINT10_START] "
            "tokens=%d top_pools_per_token=%d"
            %(len(pairs),MAX_POOLS_PER_TOKEN),
            flush=True,
        )

        hydrated=0
        failures=0
        total_quotes=0
        positive_pools=0
        best_global=None

        for token,pair in pairs.items():
            selected_pool=str(
                pair.meteora_pool
            )

            metas=_candidate_metas(
                token,
                selected_pool,
            )

            print(
                "[CHECKPOINT10_TOKEN] "
                "token=%s candidate_pools=%d selected=%s"
                %(
                    token[:12],
                    len(metas),
                    selected_pool[:12],
                ),
                flush=True,
            )

            for rank,meta in enumerate(
                metas,
                start=1,
            ):
                pool=str(meta["address"])

                try:
                    dlmm_state,arrays=_hydrate_alt(
                        meta
                    )

                    snap=_snapshot(
                        pair,
                        meta,
                        dlmm_state,
                    )

                    best,quotes,partials=(
                        _best_for_pool(
                            snap
                        )
                    )

                    hydrated+=1
                    total_quotes+=quotes

                    if best is None:
                        print(
                            "[CHECKPOINT10_POOL] "
                            "token=%s rank=%d pool=%s "
                            "arrays=%d quotes=0 partial_sizes=%d "
                            "status=NO_COMPLETE_QUOTE"
                            %(
                                token[:10],
                                rank,
                                pool[:12],
                                len(arrays),
                                partials,
                            ),
                            flush=True,
                        )
                        continue

                    positive=(
                        int(best["local_net"])>0
                    )

                    if positive:
                        positive_pools+=1

                    row={
                        "token":token,
                        "pool":pool,
                        "selected":
                            pool==selected_pool,
                        "rank":rank,
                        "arrays":len(arrays),
                        "quotes":quotes,
                        "best":best,
                    }

                    if (
                        best_global is None
                        or int(best["local_net"])
                        >int(
                            best_global[
                                "best"
                            ][
                                "local_net"
                            ]
                        )
                    ):
                        best_global=row

                    print(
                        "[CHECKPOINT10_POOL] "
                        "token=%s rank=%d pool=%s "
                        "selected=%s arrays=%d quotes=%d "
                        "best_dir=%s size=%.3f "
                        "net=%+d bps=%+.2f status=%s"
                        %(
                            token[:10],
                            rank,
                            pool[:12],
                            str(
                                pool==selected_pool
                            ),
                            len(arrays),
                            quotes,
                            best["direction"],
                            best["size_sol"],
                            int(best["local_net"]),
                            float(best["local_bps"]),
                            (
                                "GROSS_POSITIVE"
                                if positive
                                else "NONPOSITIVE"
                            ),
                        ),
                        flush=True,
                    )

                except Exception as exc:
                    failures+=1

                    print(
                        "[CHECKPOINT10_POOL_SKIP] "
                        "token=%s rank=%d pool=%s %s:%s"
                        %(
                            token[:10],
                            rank,
                            pool[:12],
                            type(exc).__name__,
                            str(exc)[:160],
                        ),
                        flush=True,
                    )

        print(
            "[CHECKPOINT10_SUMMARY] "
            "tokens=%d hydrated_pools=%d "
            "pool_failures=%d exact_quotes=%d "
            "gross_positive_pools=%d"
            %(
                len(pairs),
                hydrated,
                failures,
                total_quotes,
                positive_pools,
            ),
            flush=True,
        )

        if best_global is not None:
            best=best_global["best"]

            print(
                "[CHECKPOINT10_BEST] "
                "token=%s pool=%s selected=%s "
                "dir=%s size=%.3f net=%+d bps=%+.2f"
                %(
                    best_global["token"][:10],
                    best_global["pool"][:12],
                    str(best_global["selected"]),
                    best["direction"],
                    best["size_sol"],
                    int(best["local_net"]),
                    float(best["local_bps"]),
                ),
                flush=True,
            )

        print(
            "[CHECKPOINT10_GATE] status=%s"
            %(
                "ALTERNATE_GROSS_POSITIVE_FOUND"
                if positive_pools
                else "NO_GROSS_POSITIVE_IN_TOP_ALTERNATES"
            ),
            flush=True,
        )

        print(
            "[SCOPE] startup_static_exact_quoteability=True",
            flush=True,
        )
        print("[SIMULATION] disabled",flush=True)
        print("[BROADCAST] disabled",flush=True)

        return 0

    finally:
        pd.MAX_PAIRS=old_pair_cap
        m.MAX_ACCOUNTS=old_account_cap

        if getattr(r.q18,"_worker",None) is not None:
            r.q18._worker.close()
            r.q18._worker=None

        try:
            r.q25.q23.worker().close()
        except Exception:
            pass


if __name__=="__main__":
    raise SystemExit(main())
