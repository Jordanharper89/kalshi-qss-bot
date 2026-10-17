from __future__ import annotations

import time

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint6_all_pairs_fee_ranked_sweep as c6

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

WATCH={
    "events":0,
    "direction_quotes":0,
    "gross_positive":0,
    "compiled":0,
    "after_fee_positive":0,
    "best":None,
}


def _reverse_only(snap,size):
    token=str(snap["token"])
    start=int(round(float(size)*1e9))

    mq=r.q18.core.dlmm_quote_snapshot(
        snap,
        start,
        r.q18.core.WSOL,
    )

    token_in=r.q18.token_net(
        token,
        int(mq["raw_out"]),
    )

    if token_in<=0:
        raise RuntimeError(
            "REVERSE_TOKEN_NET_ZERO"
        )

    sell=r.q18.worker().sell(
        snap,
        token_in,
    )

    end=int(sell["uiQuote"])
    min_end=int(sell["minQuote"])

    return {
        "token":token,
        "pump_pool":snap["pump_pool"],
        "meteora":snap["meteora"],
        "start":start,
        "size_sol":float(size),
        "direction":"METEORA_TO_PUMP",
        "mq":mq,
        "gross_token":int(mq["raw_out"]),
        "net_token":token_in,
        "local_end":end,
        "local_min_end":min_end,
        "local_net":end-start,
        "local_min_net":min_end-start,
        "local_bps":(end-start)/start*10000.0,
        "local_min_bps":
            (min_end-start)/start*10000.0,
        "pump_model":"EXACT_PUMPSWAP_SDK",
    }


def _forward_only(snap,size):
    token=str(snap["token"])
    start=int(round(float(size)*1e9))

    buy=r.q18.worker().buy(
        snap,
        start,
    )

    gross=int(buy["baseOut"])

    token_in=r.q18.token_net(
        token,
        gross,
    )

    if token_in<=0:
        raise RuntimeError(
            "FORWARD_TOKEN_NET_ZERO"
        )

    mq=r.q18.core.dlmm_quote_snapshot(
        snap,
        token_in,
        token,
    )

    end=int(mq["raw_out"])

    return {
        "token":token,
        "pump_pool":snap["pump_pool"],
        "meteora":snap["meteora"],
        "start":start,
        "size_sol":float(size),
        "direction":"PUMP_TO_METEORA",
        "mq":mq,
        "pump_base_out_gross":gross,
        "pump_base_out_net":token_in,
        "pump_max_quote":int(buy["maxQuote"]),
        "local_end":end,
        "local_net":end-start,
        "local_bps":(end-start)/start*10000.0,
        "pump_model":"EXACT_PUMPSWAP_SDK",
    }


def _route(user,snap,op):
    if op["direction"]=="METEORA_TO_PUMP":
        return c6._reverse_route(
            user,
            snap,
            op,
        )

    if op["direction"]=="PUMP_TO_METEORA":
        return c6._forward_route(
            user,
            snap,
            op,
        )

    raise RuntimeError(
        "CHECKPOINT7_UNKNOWN_DIRECTION"
    )


def _record_positive(
    self,
    token,
    snap,
    op,
    slot,
    event_age_ms,
):
    WATCH["gross_positive"]+=1

    try:
        route=_route(
            r.USER,
            snap,
            op,
        )

        fee_info=c6._compiled_fee(
            r.USER,
            route,
        )

    except Exception as exc:
        print(
            "[CHECKPOINT7_COMPILE_SKIP] "
            "token=%s slot=%s size=%.3f dir=%s %s:%s"
            %(
                token[:10],
                slot,
                op["size_sol"],
                op["direction"],
                type(exc).__name__,
                str(exc)[:160],
            ),
            flush=True,
        )
        return

    if fee_info is None:
        return

    WATCH["compiled"]+=1

    after=(
        int(op["local_net"])
        -int(fee_info["fee_lamports"])
    )

    row={
        "token":token,
        "slot":slot,
        "size_sol":float(op["size_sol"]),
        "direction":op["direction"],
        "gross_net":int(op["local_net"]),
        "fee_lamports":
            int(fee_info["fee_lamports"]),
        "after_fee":int(after),
        "bytes":int(fee_info["bytes"]),
        "event_age_ms":float(event_age_ms),
        "seen_ns":time.perf_counter_ns(),
    }

    print(
        "[CHECKPOINT7_EXECUTABLE_READ] "
        "token=%s slot=%s size=%.3f dir=%s "
        "gross=%+d fee=%d after=%+d bytes=%d "
        "event_age_ms=%.3f"
        %(
            token[:10],
            slot,
            row["size_sol"],
            row["direction"],
            row["gross_net"],
            row["fee_lamports"],
            row["after_fee"],
            row["bytes"],
            row["event_age_ms"],
        ),
        flush=True,
    )

    if after<=0:
        return

    WATCH["after_fee_positive"]+=1

    previous=WATCH["best"]

    if (
        previous is None
        or int(row["after_fee"])
        >int(previous["after_fee"])
    ):
        WATCH["best"]=dict(row)

    print(
        "[CHECKPOINT7_POSITIVE_AFTER_FEE] "
        "token=%s slot=%s size=%.3f dir=%s "
        "after=%+d bps=%+.2f"
        %(
            token[:10],
            slot,
            row["size_sol"],
            row["direction"],
            row["after_fee"],
            (
                row["after_fee"]
                /(row["size_sol"]*1e9)
                *10000.0
            ),
        ),
        flush=True,
    )


def live_price(
    self,
    token,
    row,
):
    (
        snap,
        slot,
        received_ns,
        generation,
    )=row

    WATCH["events"]+=1

    event_age_ms=max(
        0.0,
        (
            time.perf_counter_ns()
            -received_ns
        )/1e6,
    )

    best_local=None

    for size in SIZES:
        for label,fn in (
            ("METEORA_TO_PUMP",_reverse_only),
            ("PUMP_TO_METEORA",_forward_only),
        ):
            if self.newer_waiting(
                token,
                generation,
            ):
                self.scan_replaced+=1
                return

            try:
                op=fn(
                    snap,
                    size,
                )
                WATCH["direction_quotes"]+=1
            except Exception as exc:
                if str(exc)=="DLMM_PARTIAL":
                    continue

                print(
                    "[CHECKPOINT7_QUOTE_SKIP] "
                    "token=%s slot=%s size=%.3f dir=%s %s:%s"
                    %(
                        token[:10],
                        slot,
                        size,
                        label,
                        type(exc).__name__,
                        str(exc)[:120],
                    ),
                    flush=True,
                )
                continue

            self.processed+=1

            if (
                best_local is None
                or int(op["local_net"])
                >int(best_local["local_net"])
            ):
                best_local=dict(op)

            if int(op["local_net"])<=0:
                continue

            self.positive+=1

            _record_positive(
                self,
                token,
                snap,
                op,
                slot,
                event_age_ms,
            )

    if best_local is not None:
        if (
            self.best is None
            or int(best_local["local_net"])
            >int(self.best["local_net"])
        ):
            self.best=dict(best_local)

        print(
            "[CHECKPOINT7_EVENT_BEST] "
            "token=%s slot=%s dir=%s size=%.3f "
            "net=%+d bps=%+.2f event_age_ms=%.3f"
            %(
                token[:10],
                slot,
                best_local["direction"],
                best_local["size_sol"],
                best_local["local_net"],
                best_local["local_bps"],
                event_age_ms,
            ),
            flush=True,
        )


def main():
    original=r.canonical_price
    r.canonical_price=live_price

    print(
        "[CHECKPOINT7_START] "
        "seconds=90 mode=EVENT_DRIVEN_ALL_PAIRS_BOTH_DIRECTIONS",
        flush=True,
    )
    print(
        "[CHECKPOINT7_COMPILE_GATE] "
        "gross_positive_only=True",
        flush=True,
    )
    print(
        "[CHECKPOINT7_FEE] real_getFeeForMessage=True",
        flush=True,
    )
    print("[SIMULATION] disabled",flush=True)
    print("[BROADCAST] disabled",flush=True)

    try:
        code=r.run(
            seconds=90.0
        )
    finally:
        r.canonical_price=original

    best=WATCH["best"]

    print(
        "[CHECKPOINT7_SUMMARY] "
        "events=%d direction_quotes=%d "
        "gross_positive=%d compiled=%d "
        "positive_after_fee=%d"
        %(
            WATCH["events"],
            WATCH["direction_quotes"],
            WATCH["gross_positive"],
            WATCH["compiled"],
            WATCH["after_fee_positive"],
        ),
        flush=True,
    )

    if best:
        print(
            "[CHECKPOINT7_BEST] "
            "token=%s slot=%s size=%.3f dir=%s "
            "gross=%+d fee=%d after=%+d bytes=%d"
            %(
                best["token"][:10],
                best["slot"],
                best["size_sol"],
                best["direction"],
                best["gross_net"],
                best["fee_lamports"],
                best["after_fee"],
                best["bytes"],
            ),
            flush=True,
        )
        print(
            "[CHECKPOINT7_GATE] "
            "status=POSITIVE_LIVE_CANDIDATE_OBSERVED",
            flush=True,
        )
    else:
        print(
            "[CHECKPOINT7_GATE] "
            "status=NO_POSITIVE_LIVE_CANDIDATE_IN_90S",
            flush=True,
        )

    return int(code or 0)


if __name__=="__main__":
    raise SystemExit(main())
