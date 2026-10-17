from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint26_dlmm_output_ata_readiness as c26
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as canonical_runtime

persistent=canonical_runtime.persistent
merged=persistent.m

MAX_CONNECTIONS=8
MIN_SHARD_SIZE=48
MAX_SHARD_SIZE=128
CONNECT_STAGGER_SECONDS=1.50

_ORIGINAL_SHARDS=None
_ORIGINAL_WORKER=None


def adaptive_shards(addresses):
    rows=list(dict.fromkeys(addresses))

    if not rows:
        return []

    connections=min(
        MAX_CONNECTIONS,
        max(
            1,
            math.ceil(
                len(rows)/MAX_SHARD_SIZE
            ),
        ),
    )

    target=max(
        MIN_SHARD_SIZE,
        math.ceil(
            len(rows)/connections
        ),
    )

    target=min(
        MAX_SHARD_SIZE,
        target,
    )

    shards=[
        rows[i:i+target]
        for i in range(
            0,
            len(rows),
            target,
        )
    ]

    if len(shards)>MAX_CONNECTIONS:
        target=math.ceil(
            len(rows)/MAX_CONNECTIONS
        )

        if target>MAX_SHARD_SIZE:
            raise RuntimeError(
                "CHECKPOINT27_ACCOUNT_SURFACE_EXCEEDS_TRANSPORT:"
                +str(len(rows))
            )

        shards=[
            rows[i:i+target]
            for i in range(
                0,
                len(rows),
                target,
            )
        ]

    if len(shards)>MAX_CONNECTIONS:
        raise RuntimeError(
            "CHECKPOINT27_CONNECTION_CAP_BREACH:"
            +str(len(shards))
        )

    if sum(len(x) for x in shards)!=len(rows):
        raise RuntimeError(
            "CHECKPOINT27_ACCOUNT_COVERAGE_MISMATCH"
        )

    print(
        "[CHECKPOINT27_PACK] "
        "accounts=%d connections=%d min_shard=%d max_shard=%d"
        %(
            len(rows),
            len(shards),
            min(len(x) for x in shards),
            max(len(x) for x in shards),
        ),
        flush=True,
    )

    return shards


def _is_rate_limit(text):
    low=str(text).lower()

    return any(
        x in low
        for x in (
            "http 429",
            "too many requests",
            "rate limit",
            "too many subscriptions",
            "1013",
        )
    )


async def bounded_worker(index,addresses,q,counters,stop):
    import websockets

    await asyncio.sleep(
        index*CONNECT_STAGGER_SECONDS
    )

    delay=float(
        persistent.RECONNECT_MIN
    )

    while not stop.is_set():
        by_id={
            i+1:a
            for i,a in enumerate(
                addresses
            )
        }

        submap={}

        try:
            async with websockets.connect(
                merged.WS_URL,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=3,
                max_size=8_000_000,
            ) as ws:

                counters["connections"]+=1

                for req in merged._req(addresses):
                    if stop.is_set():
                        break

                    await ws.send(
                        json.dumps(
                            req,
                            separators=(",",":"),
                        )
                    )

                    if merged.SUB_DELAY_MS>0:
                        await asyncio.sleep(
                            merged.SUB_DELAY_MS/1000.0
                        )

                delay=float(
                    persistent.RECONNECT_MIN
                )

                print(
                    "[CHECKPOINT27_WS_READY] "
                    "shard=%d subscriptions=%d"
                    %(
                        index,
                        len(addresses),
                    ),
                    flush=True,
                )

                while not stop.is_set():
                    try:
                        raw=await asyncio.wait_for(
                            ws.recv(),
                            timeout=1.0,
                        )

                    except asyncio.TimeoutError:
                        continue

                    msg=json.loads(raw)

                    if (
                        "id" in msg
                        and isinstance(
                            msg.get("result"),
                            int,
                        )
                    ):
                        address=by_id.get(
                            int(msg["id"])
                        )

                        if address:
                            submap[
                                int(msg["result"])
                            ]=address

                            counters["acks"]+=1

                        continue

                    ev=merged._parse(
                        msg,
                        submap,
                    )

                    if not ev:
                        continue

                    counters["notifications"]+=1

                    try:
                        q.put_nowait(ev)

                    except asyncio.QueueFull:
                        counters["queue_drops"]+=1

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            text=(
                type(exc).__name__
                +": "
                +str(exc)
            )

            counters["reconnects"]+=1
            counters["last_ws_error"]=text

            rate_limited=_is_rate_limit(text)

            if rate_limited:
                counters[
                    "rate_limit_disconnects"
                ]+=1

            print(
                "[WS_RECOVER] "
                "shard=%d rate_limited=%s error=%s retry_in=%.1fs"
                %(
                    index,
                    str(rate_limited),
                    text,
                    delay,
                ),
                flush=True,
            )

            await asyncio.sleep(delay)

            delay=min(
                float(
                    persistent.RECONNECT_MAX
                ),
                max(
                    float(
                        persistent.RECONNECT_MIN
                    ),
                    delay*2.0,
                ),
            )


def install_transport():
    global _ORIGINAL_SHARDS
    global _ORIGINAL_WORKER

    if _ORIGINAL_SHARDS is not None:
        return

    if not hasattr(
        merged,
        "_shards",
    ):
        raise RuntimeError(
            "CHECKPOINT27_SHARD_OWNER_MISSING"
        )

    if not hasattr(
        persistent,
        "_worker",
    ):
        raise RuntimeError(
            "CHECKPOINT27_WORKER_OWNER_MISSING"
        )

    _ORIGINAL_SHARDS=merged._shards
    _ORIGINAL_WORKER=persistent._worker

    merged._shards=adaptive_shards
    persistent._worker=bounded_worker


def restore_transport():
    global _ORIGINAL_SHARDS
    global _ORIGINAL_WORKER

    if _ORIGINAL_SHARDS is None:
        return

    merged._shards=_ORIGINAL_SHARDS
    persistent._worker=_ORIGINAL_WORKER

    _ORIGINAL_SHARDS=None
    _ORIGINAL_WORKER=None


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
            "CHECKPOINT27_SECONDS_MUST_BE_POSITIVE"
        )

    old_argv=list(sys.argv)

    install_transport()

    print(
        "[CHECKPOINT27_ACTIVATION] "
        "bounded_adaptive_ws_transport=True "
        "max_connections=%d"
        %MAX_CONNECTIONS,
        flush=True,
    )

    print(
        "[CHECKPOINT27_OWNER] "
        "runtime.persistent._worker + "
        "runtime.persistent.m._shards",
        flush=True,
    )

    print(
        "[CHECKPOINT27_SURFACE] "
        "full_account_coverage=True "
        "pair_surface_not_reduced=True",
        flush=True,
    )

    print(
        "[CHECKPOINT27_RATE_LIMITS] "
        "http_429_counted=True "
        "too_many_requests_counted=True",
        flush=True,
    )

    print(
        "[CHECKPOINT27_CHAIN] "
        "checkpoint26 -> expanded 76-pair universe -> "
        "bounded WS transport -> exact pricing -> "
        "canonical ALT -> real fee -> freshness -> signed sim",
        flush=True,
    )

    print(
        "[BROADCAST] disabled",
        flush=True,
    )

    try:
        sys.argv=[
            old_argv[0],
            "--seconds",
            str(float(args.seconds)),
        ]

        return c26.main()

    finally:
        sys.argv=old_argv
        restore_transport()

        print(
            "[CHECKPOINT27_TRANSPORT_RESTORED] true",
            flush=True,
        )


if __name__=="__main__":
    raise SystemExit(main())
