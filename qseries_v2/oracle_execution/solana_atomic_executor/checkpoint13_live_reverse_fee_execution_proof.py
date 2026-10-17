from __future__ import annotations

import asyncio
import base64
import time
import urllib.error

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint12_multi_pool_live_size_optimizer as c12

SECONDS=90.0

WATCH={
    "quotes":0,
    "gross_positive":0,
    "reverse_positive":0,
    "compiled":0,
    "fee_positive":0,
    "best_gross":None,
    "best_after_fee":None,
}

USER=None


def _fee_for_message(compiled):
    msg=compiled.get("msg")
    if msg is None:
        raise RuntimeError("CHECKPOINT13_COMPILED_MESSAGE_MISSING")

    encoded=base64.b64encode(bytes(msg)).decode()
    last=None

    for attempt in range(1,7):
        try:
            result=r.q87.c.rpc(
                "getFeeForMessage",
                [encoded,{"commitment":"processed"}],
            )
            if not isinstance(result,dict):
                raise RuntimeError("CHECKPOINT13_FEE_RESULT_NOT_MAPPING")
            fee=result.get("value")
            if fee is None:
                raise RuntimeError("CHECKPOINT13_FEE_VALUE_NONE")
            return int(fee)

        except urllib.error.HTTPError as exc:
            last=exc
            if getattr(exc,"code",None)!=429:
                raise
            delay=min(4.0,.50*(2**(attempt-1)))
            print(
                "[CHECKPOINT13_FEE_429] attempt=%d sleep=%.2fs"
                %(attempt,delay),
                flush=True,
            )
            time.sleep(delay)

    raise last or RuntimeError("CHECKPOINT13_FEE_429_EXHAUSTED")


def _compile_reverse(user,snap,opportunity):
    if opportunity.get("direction")!="METEORA_TO_PUMP":
        raise RuntimeError("CHECKPOINT13_REVERSE_ONLY")

    route=c7._route(user,snap,opportunity)
    compiled=r.compile_current(user,route)

    if not compiled.get("ok"):
        return {
            "ok":False,
            "reason":compiled.get("reason","UNKNOWN_COMPILE_REJECT"),
            "compiled":compiled,
        }

    fee=_fee_for_message(compiled)
    gross=int(opportunity["local_net"])
    after_fee=gross-fee

    return {
        "ok":True,
        "compiled":compiled,
        "fee":fee,
        "gross":gross,
        "after_fee":after_fee,
    }


def _price(self,identity,row):
    snap,slot,received_ns,generation=row
    token=str(snap["token"])
    pool=str(snap["meteora"]["address"])

    for size in c12.SIZES:
        for fn in (c7._reverse_only,c7._forward_only):
            if self.newer_waiting(identity,generation):
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

            candidate=dict(op)
            candidate["pair_key"]=identity
            candidate["meteora_pool"]=pool
            candidate["slot"]=slot

            if (
                WATCH["best_gross"] is None
                or int(candidate["local_net"])
                >int(WATCH["best_gross"]["local_net"])
            ):
                WATCH["best_gross"]=dict(candidate)

            if int(candidate["local_net"])<=0:
                continue

            WATCH["gross_positive"]+=1

            print(
                "[CHECKPOINT13_GROSS_POSITIVE] "
                "pair=%s token=%s pool=%s slot=%s dir=%s "
                "size=%.3f gross=%+d bps=%+.2f"
                %(
                    identity[:28],
                    token[:10],
                    pool[:12],
                    slot,
                    candidate["direction"],
                    candidate["size_sol"],
                    int(candidate["local_net"]),
                    float(candidate["local_bps"]),
                ),
                flush=True,
            )

            if candidate["direction"]!="METEORA_TO_PUMP":
                print(
                    "[CHECKPOINT13_FORWARD_HOLD] pair=%s size=%.3f"
                    %(identity[:28],candidate["size_sol"]),
                    flush=True,
                )
                continue

            WATCH["reverse_positive"]+=1

            if self.newer_waiting(identity,generation):
                self.scan_replaced+=1
                return

            try:
                proof=_compile_reverse(USER,snap,candidate)
            except Exception as exc:
                print(
                    "[CHECKPOINT13_PROOF_ERROR] "
                    "pair=%s size=%.3f %s:%s"
                    %(
                        identity[:28],
                        candidate["size_sol"],
                        type(exc).__name__,
                        str(exc)[:220],
                    ),
                    flush=True,
                )
                continue

            if not proof.get("ok"):
                print(
                    "[CHECKPOINT13_COMPILE_HOLD] pair=%s size=%.3f reason=%s"
                    %(identity[:28],candidate["size_sol"],proof.get("reason")),
                    flush=True,
                )
                continue

            WATCH["compiled"]+=1
            compiled=proof["compiled"]

            print(
                "[CHECKPOINT13_FEE_PROOF] "
                "pair=%s slot=%s size=%.3f gross=%+d fee=%d "
                "after_fee=%+d bytes=%d candidate=%s"
                %(
                    identity[:28],
                    slot,
                    candidate["size_sol"],
                    proof["gross"],
                    proof["fee"],
                    proof["after_fee"],
                    int(compiled["bytes"]),
                    str(compiled["candidate"]),
                ),
                flush=True,
            )

            row2=dict(candidate)
            row2["fee"]=proof["fee"]
            row2["after_fee"]=proof["after_fee"]
            row2["bytes"]=int(compiled["bytes"])
            row2["compile_candidate"]=str(compiled["candidate"])

            if (
                WATCH["best_after_fee"] is None
                or int(row2["after_fee"])
                >int(WATCH["best_after_fee"]["after_fee"])
            ):
                WATCH["best_after_fee"]=row2

            if proof["after_fee"]>0:
                WATCH["fee_positive"]+=1
                print(
                    "[CHECKPOINT13_FEE_POSITIVE] pair=%s size=%.3f after_fee=%+d"
                    %(identity[:28],candidate["size_sol"],proof["after_fee"]),
                    flush=True,
                )


def main():
    global USER

    old_process=r.process_event
    old_price=r.canonical_price
    old_ready=set(r.READY_TOKENS)
    lane=None

    try:
        state,registry,failures=c12._expanded_state()

        r.q25.install_hot_math_and_prewarm(state)
        r.q18.install_exact_hot_math()

        unique_pumps=[]
        for pair in state["pairs"]:
            pool=str(pair.pump_pool)
            if pool in unique_pumps:
                continue
            unique_pumps.append(pool)
            r.q18.worker().warm(pool)

        _,USER=r.q87.c.sim_identity()
        r.BLOCKHASH.start()

        r.READY_TOKENS={
            c12.pair_key(pair)
            for pair in state["pairs"]
        }

        r.process_event=c12._process_event
        r.canonical_price=_price

        lane=r.q20.LatestStateLane()
        lane._price=_price.__get__(lane,r.q20.LatestStateLane)
        lane.start()

        print(
            "[CHECKPOINT13_START] seconds=90 reverse_only_compile=True "
            "fee_readback=True simulation=False broadcast=False",
            flush=True,
        )
        print(
            "[CHECKPOINT13_UNIVERSE] registry_pairs=%d live_pairs=%d "
            "hydrate_failures=%d accounts=%d"
            %(
                int(registry.get("ready_pair_count") or len(registry.get("rows") or [])),
                len(state["pairs"]),
                len(failures),
                len(state["addresses"]),
            ),
            flush=True,
        )
        print(
            "[CHECKPOINT13_SIZES] "
            "0.001,0.010,0.025,0.050,0.100,0.180,0.280,0.500,1.000,1.400",
            flush=True,
        )
        print(
            "[CHECKPOINT13_SELECTION] gross_all_sizes=True "
            "reverse_positive_advances_to_fee=True rank_after_real_fee=True",
            flush=True,
        )
        print("[SIMULATION] disabled",flush=True)
        print("[BROADCAST] disabled",flush=True)

        asyncio.run(r.serve_canonical(state,SECONDS,lane))

        print(
            "[CHECKPOINT13_SUMMARY] quotes=%d gross_positive=%d "
            "reverse_positive=%d compiled=%d fee_positive=%d "
            "processed=%d scan_replaced=%d"
            %(
                WATCH["quotes"],
                WATCH["gross_positive"],
                WATCH["reverse_positive"],
                WATCH["compiled"],
                WATCH["fee_positive"],
                lane.processed,
                lane.scan_replaced,
            ),
            flush=True,
        )

        best=WATCH["best_after_fee"]
        if best is not None:
            print(
                "[CHECKPOINT13_BEST_AFTER_FEE] "
                "pair=%s token=%s pool=%s dir=%s size=%.3f "
                "gross=%+d fee=%d after_fee=%+d bps=%+.2f "
                "bytes=%d candidate=%s"
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
                    int(best["bytes"]),
                    best["compile_candidate"],
                ),
                flush=True,
            )

        print(
            "[CHECKPOINT13_GATE] status=%s"
            %(
                "REAL_FEE_POSITIVE_REVERSE_OBSERVED"
                if WATCH["fee_positive"]>0
                else "NO_REAL_FEE_POSITIVE_REVERSE_IN_90S"
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
