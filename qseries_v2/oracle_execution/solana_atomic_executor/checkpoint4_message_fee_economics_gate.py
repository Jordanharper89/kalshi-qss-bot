from __future__ import annotations

import base64
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint2_forward_atomic_sim as cp
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint3_reverse_atomic_compile as c3


class _Checkpoint4Complete(Exception):
    pass


def _message_fee_lamports(compiled):
    msg=compiled.get("msg")
    if msg is None:
        raise RuntimeError("CHECKPOINT4_MESSAGE_MISSING")

    encoded=base64.b64encode(bytes(msg)).decode()

    import time
    import urllib.error

    last=None

    for attempt in range(6):
        try:
            result=r.q87.c.rpc(
                "getFeeForMessage",
                [
                    encoded,
                    {
                        "commitment":"processed",
                    },
                ],
            )
            break
        except urllib.error.HTTPError as exc:
            last=exc

            if getattr(exc,"code",None)!=429:
                raise

            delay=min(
                4.0,
                0.50*(2**attempt),
            )

            print(
                "[CHECKPOINT4_FEE_429_RETRY] "
                "attempt=%d sleep=%.2fs"
                %(
                    attempt+1,
                    delay,
                ),
                flush=True,
            )

            time.sleep(delay)
    else:
        raise last or RuntimeError(
            "CHECKPOINT4_FEE_RPC_RETRY_EXHAUSTED"
        )

    if not isinstance(result,dict):
        raise RuntimeError("CHECKPOINT4_FEE_RESULT_NOT_MAPPING")

    value=result.get("value")

    if value is None:
        raise RuntimeError("CHECKPOINT4_FEE_UNAVAILABLE")

    fee=int(value)

    if fee < 0:
        raise RuntimeError("CHECKPOINT4_NEGATIVE_FEE")

    return fee


def evaluate(user,snap):
    reverse=c3._reverse_opportunity(snap)
    route=c3._reverse_route(user,snap,reverse)

    compiled=r.compile_current(
        user,
        route,
    )

    if not compiled.get("ok"):
        print(
            "[CHECKPOINT4_COMPILE_FAIL] %s"%compiled,
            flush=True,
        )
        return {
            "ok":False,
            "phase":"compile",
            "compiled":compiled,
        }

    fee=_message_fee_lamports(compiled)

    gross=int(reverse["local_net"])
    after=gross-fee
    start=int(reverse["start"])
    after_bps=(
        after/start*10000.0
        if start>0
        else 0.0
    )

    print(
        "[CHECKPOINT4_MESSAGE_FEE] "
        "lamports=%d"%fee,
        flush=True,
    )
    print(
        "[CHECKPOINT4_ECONOMICS] "
        "direction=METEORA_TO_PUMP "
        "gross_net=%+d "
        "message_fee=%d "
        "after_message_fee=%+d "
        "after_message_fee_bps=%+.2f"
        %(
            gross,
            fee,
            after,
            after_bps,
        ),
        flush=True,
    )

    admitted=after>0

    print(
        "[CHECKPOINT4_GATE] "
        "status=%s"
        %(
            "PASS_POSITIVE_AFTER_MESSAGE_FEE"
            if admitted
            else "HOLD_NONPOSITIVE_AFTER_MESSAGE_FEE"
        ),
        flush=True,
    )

    print(
        "[CHECKPOINT4_SCOPE] "
        "message_fee_only=True "
        "priority_fee_and_simulation_pending=True",
        flush=True,
    )
    print("[BROADCAST] disabled",flush=True)

    return {
        "ok":True,
        "direction":"METEORA_TO_PUMP",
        "bytes":int(compiled.get("bytes") or 0),
        "gross_net_lamports":gross,
        "message_fee_lamports":fee,
        "after_message_fee_lamports":after,
        "after_message_fee_bps":after_bps,
        "admitted":admitted,
        "simulation":False,
        "broadcast":False,
    }


def main():
    captured={}
    original=r._execute_route_once

    def intercept(user,snap,_forward):
        captured["result"]=evaluate(user,snap)
        raise _Checkpoint4Complete()

    r._execute_route_once=intercept

    try:
        try:
            cp.main()
        except _Checkpoint4Complete:
            pass
    finally:
        r._execute_route_once=original

    result=captured.get("result")

    if not isinstance(result,dict):
        raise RuntimeError(
            "CHECKPOINT4_ROUTE_NOT_MATERIALIZED"
        )

    if not result.get("ok"):
        return 1

    print(
        "[CHECKPOINT4_FINAL] "
        "status=PASS_MEASUREMENT "
        "admitted=%s"
        %str(bool(result.get("admitted"))),
        flush=True,
    )

    return 0


if __name__=="__main__":
    raise SystemExit(main())
