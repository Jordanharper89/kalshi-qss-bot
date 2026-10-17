from __future__ import annotations

import asyncio
import time

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint12_multi_pool_live_size_optimizer as c12
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint13_live_reverse_fee_execution_proof as c13
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint14_fee_positive_signed_simulation as c14

SECONDS=90.0
MAX_EVENT_AGE_MS=1500.0

WATCH={
    "quotes":0,
    "gross_positive":0,
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

USER=None


def _compile_all_legal(user,route,gross):
    blockhash=r.BLOCKHASH.get()
    rows=[]

    for candidate in list(
        r.q87.repaired_candidates(route)
    ):
        name=str(
            candidate.get("name","UNKNOWN")
        )

        if "PUMP_METEORA_ONLY" in name:
            continue

        try:
            comp=r.q87.compile_candidate(
                user,
                candidate["instructions"],
                [[]],
                blockhash,
            )
        except Exception as exc:
            print(
                "[CHECKPOINT15_COMPILE_ERROR] "
                "candidate=%s %s:%s"
                %(
                    name,
                    type(exc).__name__,
                    str(exc)[:180],
                ),
                flush=True,
            )
            continue

        if not isinstance(comp,dict) or not comp.get("ok"):
            continue

        raw=comp["unsigned"]
        size=len(raw)

        print(
            "[CHECKPOINT15_COMPILED] "
            "candidate=%s bytes=%d"
            %(name,size),
            flush=True,
        )

        if size>r.MAX_TX_BYTES:
            print(
                "[CHECKPOINT15_SIZE_HOLD] "
                "candidate=%s bytes=%d"
                %(name,size),
                flush=True,
            )
            continue

        WATCH["candidate_compiles"]+=1

        compiled={
            "ok":True,
            "candidate":name,
            "bytes":size,
            "msg":comp["msg"],
            "raw":raw,
        }

        try:
            fee=c13._fee_for_message(
                compiled
            )
        except Exception as exc:
            print(
                "[CHECKPOINT15_FEE_ERROR] "
                "candidate=%s %s:%s"
                %(
                    name,
                    type(exc).__name__,
                    str(exc)[:180],
                ),
                flush=True,
            )
            continue

        WATCH["candidate_fees"]+=1
        after_fee=int(gross)-int(fee)

        print(
            "[CHECKPOINT15_CANDIDATE] "
            "candidate=%s bytes=%d fee=%d "
            "gross=%+d after_fee=%+d"
            %(
                name,
                size,
                fee,
                gross,
                after_fee,
            ),
            flush=True,
        )

        rows.append({
            "compiled":compiled,
            "fee":int(fee),
            "after_fee":int(after_fee),
        })

    if not rows:
        return None

    return max(
        rows,
        key=lambda x:int(
            x["after_fee"]
        ),
    )


def _price(self,identity,row):
    snap,slot,received_ns,generation=row
    token=str(snap["token"])
    pool=str(snap["meteora"]["address"])

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

            print(
                "[CHECKPOINT15_GROSS_POSITIVE] "
                "pair=%s token=%s pool=%s slot=%s "
                "dir=%s size=%.3f gross=%+d bps=%+.2f"
                %(
                    identity[:28],
                    token[:10],
                    pool[:12],
                    slot,
                    op["direction"],
                    size,
                    int(op["local_net"]),
                    float(op["local_bps"]),
                ),
                flush=True,
            )

            if op["direction"]!="METEORA_TO_PUMP":
                continue

            age=max(
                0.0,
                (
                    time.perf_counter_ns()
                    -received_ns
                )/1e6
            )

            if age>MAX_EVENT_AGE_MS:
                WATCH["stale_holds"]+=1
                continue

            if self.newer_waiting(
                identity,
                generation,
            ):
                WATCH["superseded_holds"]+=1
                self.scan_replaced+=1
                return

            try:
                route=c7._route(
                    USER,
                    snap,
                    op,
                )

                winner=_compile_all_legal(
                    USER,
                    route,
                    int(op["local_net"]),
                )

            except Exception as exc:
                print(
                    "[CHECKPOINT15_ROUTE_ERROR] "
                    "pair=%s size=%.3f %s:%s"
                    %(
                        identity[:28],
                        size,
                        type(exc).__name__,
                        str(exc)[:220],
                    ),
                    flush=True,
                )
                continue

            if winner is None:
                print(
                    "[CHECKPOINT15_NO_LEGAL_CANDIDATE] "
                    "pair=%s size=%.3f"
                    %(identity[:28],size),
                    flush=True,
                )
                continue

            compiled=winner["compiled"]

            print(
                "[CHECKPOINT15_WINNER] "
                "pair=%s size=%.3f candidate=%s "
                "bytes=%d fee=%d gross=%+d after_fee=%+d"
                %(
                    identity[:28],
                    size,
                    compiled["candidate"],
                    compiled["bytes"],
                    winner["fee"],
                    int(op["local_net"]),
                    winner["after_fee"],
                ),
                flush=True,
            )

            if winner["after_fee"]<=0:
                print(
                    "[CHECKPOINT15_FEE_HOLD] "
                    "pair=%s size=%.3f after_fee=%+d"
                    %(
                        identity[:28],
                        size,
                        winner["after_fee"],
                    ),
                    flush=True,
                )
                continue

            WATCH["fee_positive"]+=1

            bestrow=dict(op)
            bestrow.update({
                "pair_key":identity,
                "meteora_pool":pool,
                "fee":winner["fee"],
                "after_fee":winner["after_fee"],
                "bytes":compiled["bytes"],
                "candidate":compiled["candidate"],
            })

            if (
                WATCH["best_after_fee"] is None
                or int(bestrow["after_fee"])
                >
                int(
                    WATCH[
                        "best_after_fee"
                    ][
                        "after_fee"
                    ]
                )
            ):
                WATCH["best_after_fee"]=bestrow

            if self.newer_waiting(
                identity,
                generation,
            ):
                WATCH["superseded_holds"]+=1
                self.scan_replaced+=1
                return

            age=max(
                0.0,
                (
                    time.perf_counter_ns()
                    -received_ns
                )/1e6
            )

            if age>MAX_EVENT_AGE_MS:
                WATCH["stale_holds"]+=1
                print(
                    "[CHECKPOINT15_PRE_SIM_STALE] "
                    "pair=%s size=%.3f age_ms=%.3f"
                    %(identity[:28],size,age),
                    flush=True,
                )
                continue

            WATCH["sim_attempts"]+=1

            try:
                sim=c14._signed_simulation(
                    compiled
                )
            except Exception as exc:
                WATCH["sim_fail"]+=1
                print(
                    "[CHECKPOINT15_SIM_ERROR] "
                    "pair=%s size=%.3f %s:%s"
                    %(
                        identity[:28],
                        size,
                        type(exc).__name__,
                        str(exc)[:220],
                    ),
                    flush=True,
                )
                continue

            if sim["err"] is None:
                WATCH["sim_pass"]+=1

                print(
                    "[CHECKPOINT15_SIGNED_SIM_PASS] "
                    "pair=%s token=%s pool=%s slot=%s "
                    "size=%.3f gross=%+d fee=%d after_fee=%+d "
                    "bps=%+.2f candidate=%s bytes=%d units=%s age_ms=%.3f"
                    %(
                        identity[:28],
                        token[:10],
                        pool[:12],
                        slot,
                        size,
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
                    "[CHECKPOINT15_SIGNED_SIM_FAIL] "
                    "pair=%s size=%.3f candidate=%s "
                    "after_fee=%+d err=%s units=%s"
                    %(
                        identity[:28],
                        size,
                        compiled["candidate"],
                        winner["after_fee"],
                        str(sim["err"]),
                        str(sim["units"]),
                    ),
                    flush=True,
                )

                for line in sim["logs"][-8:]:
                    print(
                        "[CHECKPOINT15_SIM_LOG] "
                        +str(line),
                        flush=True,
                    )


def main():
    global USER

    old_process=r.process_event
    old_price=r.canonical_price
    old_ready=set(r.READY_TOKENS)

    lane=None

    try:
        state,registry,failures=(
            c12._expanded_state()
        )

        r.q25.install_hot_math_and_prewarm(
            state
        )

        r.q18.install_exact_hot_math()

        seen=set()

        for pair in state["pairs"]:
            pump=str(pair.pump_pool)

            if pump in seen:
                continue

            seen.add(pump)
            r.q18.worker().warm(pump)

        c14.SIGNER,USER=(
            r.q87.c.sim_identity()
        )

        if c14.SIGNER is None or not USER:
            raise RuntimeError(
                "CHECKPOINT15_SIGNER_UNAVAILABLE"
            )

        r.BLOCKHASH.start()

        r.READY_TOKENS={
            c12.pair_key(pair)
            for pair in state["pairs"]
        }

        r.process_event=c12._process_event
        r.canonical_price=_price

        lane=r.q20.LatestStateLane()

        lane._price=_price.__get__(
            lane,
            r.q20.LatestStateLane,
        )

        lane.start()

        print(
            "[CHECKPOINT15_START] "
            "seconds=90 compare_all_legal_reverse_candidates=True "
            "real_fee_each=True signed_sim_winner_only=True broadcast=False",
            flush=True,
        )

        print(
            "[CHECKPOINT15_UNIVERSE] "
            "registry_pairs=%d live_pairs=%d "
            "hydrate_failures=%d accounts=%d"
            %(
                int(
                    registry.get("ready_pair_count")
                    or len(
                        registry.get("rows")
                        or []
                    )
                ),
                len(state["pairs"]),
                len(failures),
                len(state["addresses"]),
            ),
            flush=True,
        )

        print(
            "[CHECKPOINT15_SELECTION] "
            "winner=max(gross-real_message_fee) "
            "first_legal_candidate=False",
            flush=True,
        )

        print(
            "[CHECKPOINT15_SIZES] "
            "0.001,0.010,0.025,0.050,0.100,"
            "0.180,0.280,0.500,1.000,1.400",
            flush=True,
        )

        print("[BROADCAST] disabled",flush=True)

        asyncio.run(
            r.serve_canonical(
                state,
                SECONDS,
                lane,
            )
        )

        print(
            "[CHECKPOINT15_SUMMARY] "
            "quotes=%d gross_positive=%d "
            "candidate_compiles=%d candidate_fees=%d "
            "fee_positive=%d sim_attempts=%d "
            "sim_pass=%d sim_fail=%d "
            "stale_holds=%d superseded_holds=%d"
            %(
                WATCH["quotes"],
                WATCH["gross_positive"],
                WATCH["candidate_compiles"],
                WATCH["candidate_fees"],
                WATCH["fee_positive"],
                WATCH["sim_attempts"],
                WATCH["sim_pass"],
                WATCH["sim_fail"],
                WATCH["stale_holds"],
                WATCH["superseded_holds"],
            ),
            flush=True,
        )

        best=WATCH["best_after_fee"]

        if best is not None:
            print(
                "[CHECKPOINT15_BEST_AFTER_FEE] "
                "pair=%s token=%s pool=%s dir=%s "
                "size=%.3f gross=%+d fee=%d after_fee=%+d "
                "bps=%+.2f candidate=%s bytes=%d"
                %(
                    best["pair_key"][:28],
                    best["token"][:10],
                    best["meteora_pool"][:12],
                    best["direction"],
                    best["size_sol"],
                    int(best["local_net"]),
                    int(best["fee"]),
                    int(best["after_fee"]),
                    float(best["local_bps"]),
                    best["candidate"],
                    int(best["bytes"]),
                ),
                flush=True,
            )

        print(
            "[CHECKPOINT15_GATE] status=%s"
            %(
                "CHEAPEST_LEGAL_SIGNED_SIM_PASS"
                if WATCH["sim_pass"]>0
                else
                "NO_CHEAPEST_LEGAL_SIGNED_SIM_PASS_IN_90S"
            ),
            flush=True,
        )

        return 0

    finally:
        r.process_event=old_process
        r.canonical_price=old_price
        r.READY_TOKENS=old_ready

        try:
            r.BLOCKHASH.close()
        except Exception:
            pass

        if lane is not None:
            lane.close()

        if getattr(r.q18,"_worker",None) is not None:
            r.q18._worker.close()
            r.q18._worker=None

        try:
            r.q25.q23.worker().close()
        except Exception:
            pass


if __name__=="__main__":
    raise SystemExit(main())
