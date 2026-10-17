from __future__ import annotations

import argparse
import time

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint12_multi_pool_live_size_optimizer as c12
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint14_fee_positive_signed_simulation as c14
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint15_cheapest_legal_fee_signed_simulation as c15
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint17_pair_key_execution_templates as c17

MAX_EVENT_AGE_MS=1500.0

WATCH={
    "quotes":0,
    "gross_positive":0,
    "reverse_positive":0,
    "ranked_snapshots":0,
    "candidate_compiles":0,
    "candidate_fees":0,
    "fee_positive":0,
    "sim_attempts":0,
    "sim_pass":0,
    "sim_fail":0,
    "stale_holds":0,
    "superseded_holds":0,
    "best_after_fee":None,
}


def _price(self,identity,row):
    snap,slot,received_ns,generation=row
    token=str(snap["token"])
    pool=str(snap["meteora"]["address"])

    rows=[]

    for size in c12.SIZES:
        for fn in (
            c7._reverse_only,
            c7._forward_only,
        ):
            if self.newer_waiting(
                identity,
                generation,
            ):
                WATCH["superseded_holds"]+=1
                self.scan_replaced+=1
                return

            try:
                op=fn(snap,size)
            except RuntimeError as exc:
                if str(exc)=="DLMM_PARTIAL":
                    continue
                raise

            WATCH["quotes"]+=1
            self.processed+=1

            if int(op["local_net"])<=0:
                continue

            WATCH["gross_positive"]+=1

            if op["direction"]=="METEORA_TO_PUMP":
                WATCH["reverse_positive"]+=1
                rows.append(dict(op))
            else:
                print(
                    "[CHECKPOINT18_FORWARD_HOLD] "
                    "pair=%s size=%.3f gross=%+d bps=%+.2f"
                    %(
                        identity[:28],
                        size,
                        int(op["local_net"]),
                        float(op["local_bps"]),
                    ),
                    flush=True,
                )

    if not rows:
        return

    WATCH["ranked_snapshots"]+=1

    rows.sort(
        key=lambda x:int(x["local_net"]),
        reverse=True,
    )

    print(
        "[CHECKPOINT18_RANKED] "
        "pair=%s slot=%s candidates=%d "
        "best_size=%.3f best_gross=%+d best_bps=%+.2f"
        %(
            identity[:28],
            slot,
            len(rows),
            rows[0]["size_sol"],
            int(rows[0]["local_net"]),
            float(rows[0]["local_bps"]),
        ),
        flush=True,
    )

    for rank,op in enumerate(rows,1):
        if self.newer_waiting(
            identity,
            generation,
        ):
            WATCH["superseded_holds"]+=1
            self.scan_replaced+=1
            return

        age=max(
            0.0,
            (time.perf_counter_ns()-received_ns)/1e6,
        )

        if age>MAX_EVENT_AGE_MS:
            WATCH["stale_holds"]+=1
            print(
                "[CHECKPOINT18_STALE_HOLD] "
                "pair=%s rank=%d size=%.3f age_ms=%.3f"
                %(
                    identity[:28],
                    rank,
                    op["size_sol"],
                    age,
                ),
                flush=True,
            )
            return

        print(
            "[CHECKPOINT18_TRY] "
            "pair=%s rank=%d size=%.3f gross=%+d bps=%+.2f age_ms=%.3f"
            %(
                identity[:28],
                rank,
                op["size_sol"],
                int(op["local_net"]),
                float(op["local_bps"]),
                age,
            ),
            flush=True,
        )

        try:
            route=c7._route(
                c15.USER,
                snap,
                op,
            )

            before_compiles=(
                c15.WATCH["candidate_compiles"]
            )
            before_fees=(
                c15.WATCH["candidate_fees"]
            )

            winner=c15._compile_all_legal(
                c15.USER,
                route,
                int(op["local_net"]),
            )

            WATCH["candidate_compiles"]+=(
                c15.WATCH["candidate_compiles"]
                -before_compiles
            )
            WATCH["candidate_fees"]+=(
                c15.WATCH["candidate_fees"]
                -before_fees
            )

        except Exception as exc:
            print(
                "[CHECKPOINT18_ROUTE_ERROR] "
                "pair=%s rank=%d size=%.3f %s:%s"
                %(
                    identity[:28],
                    rank,
                    op["size_sol"],
                    type(exc).__name__,
                    str(exc)[:220],
                ),
                flush=True,
            )
            continue

        if winner is None:
            continue

        compiled=winner["compiled"]

        print(
            "[CHECKPOINT18_WINNER] "
            "pair=%s rank=%d size=%.3f candidate=%s "
            "bytes=%d fee=%d gross=%+d after_fee=%+d"
            %(
                identity[:28],
                rank,
                op["size_sol"],
                compiled["candidate"],
                compiled["bytes"],
                winner["fee"],
                int(op["local_net"]),
                winner["after_fee"],
            ),
            flush=True,
        )

        if winner["after_fee"]<=0:
            continue

        WATCH["fee_positive"]+=1

        best=dict(op)
        best.update({
            "pair_key":identity,
            "meteora_pool":pool,
            "fee":winner["fee"],
            "after_fee":winner["after_fee"],
            "bytes":compiled["bytes"],
            "candidate":compiled["candidate"],
        })

        if (
            WATCH["best_after_fee"] is None
            or int(best["after_fee"])
            >
            int(WATCH["best_after_fee"]["after_fee"])
        ):
            WATCH["best_after_fee"]=best

        if self.newer_waiting(
            identity,
            generation,
        ):
            WATCH["superseded_holds"]+=1
            self.scan_replaced+=1

            print(
                "[CHECKPOINT18_PRE_SIM_SUPERSEDED] "
                "pair=%s size=%.3f"
                %(
                    identity[:28],
                    op["size_sol"],
                ),
                flush=True,
            )
            return

        age=max(
            0.0,
            (time.perf_counter_ns()-received_ns)/1e6,
        )

        if age>MAX_EVENT_AGE_MS:
            WATCH["stale_holds"]+=1

            print(
                "[CHECKPOINT18_PRE_SIM_STALE] "
                "pair=%s size=%.3f age_ms=%.3f"
                %(
                    identity[:28],
                    op["size_sol"],
                    age,
                ),
                flush=True,
            )
            return

        WATCH["sim_attempts"]+=1

        try:
            sim=c14._signed_simulation(
                compiled
            )
        except Exception as exc:
            WATCH["sim_fail"]+=1

            print(
                "[CHECKPOINT18_SIM_ERROR] "
                "pair=%s size=%.3f %s:%s"
                %(
                    identity[:28],
                    op["size_sol"],
                    type(exc).__name__,
                    str(exc)[:220],
                ),
                flush=True,
            )
            return

        if sim["err"] is None:
            WATCH["sim_pass"]+=1

            print(
                "[CHECKPOINT18_SIGNED_SIM_PASS] "
                "pair=%s token=%s pool=%s slot=%s "
                "size=%.3f gross=%+d fee=%d after_fee=%+d "
                "bps=%+.2f candidate=%s bytes=%d units=%s age_ms=%.3f"
                %(
                    identity[:28],
                    token[:10],
                    pool[:12],
                    slot,
                    op["size_sol"],
                    int(op["local_net"]),
                    winner["fee"],
                    winner["after_fee"],
                    float(op["local_bps"]),
                    compiled["candidate"],
                    compiled["bytes"],
                    str(sim["units"]),
                    age,
                ),
                flush=True,
            )
        else:
            WATCH["sim_fail"]+=1

            print(
                "[CHECKPOINT18_SIGNED_SIM_FAIL] "
                "pair=%s size=%.3f after_fee=%+d "
                "err=%s units=%s"
                %(
                    identity[:28],
                    op["size_sol"],
                    winner["after_fee"],
                    str(sim["err"]),
                    str(sim["units"]),
                ),
                flush=True,
            )

            for line in sim["logs"][-8:]:
                print(
                    "[CHECKPOINT18_SIM_LOG] "
                    +str(line),
                    flush=True,
                )

        return


def main():
    p=argparse.ArgumentParser()
    p.add_argument(
        "--seconds",
        type=float,
        default=3600.0,
    )
    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError(
            "CHECKPOINT18_SECONDS_MUST_BE_POSITIVE"
        )

    old_price=c15._price

    try:
        c15._price=_price

        print(
            "[CHECKPOINT18_ACTIVATION] "
            "snapshot_best_first=True "
            "full_ladder_before_rpc=True "
            "seconds=%.0f broadcast=False"
            %args.seconds,
            flush=True,
        )

        print(
            "[CHECKPOINT18_SELECTION] "
            "reverse_positive_sizes=rank_by_gross_desc "
            "compile_fee_best_first=True "
            "fallback_next_size=True",
            flush=True,
        )

        rc=c17.main_with_seconds(
            float(args.seconds)
        ) if hasattr(
            c17,
            "main_with_seconds"
        ) else None

        if rc is not None:
            return rc

        import sys

        old_argv=list(sys.argv)

        try:
            sys.argv=[
                old_argv[0],
                "--seconds",
                str(float(args.seconds)),
            ]

            return c17.main()

        finally:
            sys.argv=old_argv

    finally:
        c15._price=old_price


if __name__=="__main__":
    raise SystemExit(main())
