from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

import websockets

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import (
    core as c
)

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_043b_paced_mriya_token_discovery
    as mriya
)


EXECUTION_AUTHORITY=False
READ_ONLY=True

STATE=Path(
    "runtime_state/oracle/"
    "oracle_live_execution/"
    "oracle_013_pumpswap_program_tokens.json"
)

PUMP=c.PUMP
WSOL=c.WSOL

QUEUE_MAX=int(
    os.getenv(
        "ORACLE_PUMP_DISCOVERY_QUEUE_MAX",
        "3000"
    )
)


def load():
    if not STATE.is_file():
        return {
            "tokens":{},
            "signatures":[],
        }

    try:
        return json.loads(
            STATE.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return {
            "tokens":{},
            "signatures":[],
        }


def save(data):
    STATE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tmp=STATE.with_name(
        STATE.name
        +".%d.tmp"%os.getpid()
    )

    tmp.write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )

    os.replace(
        tmp,
        STATE
    )


def ingest(
    signature,
    tx,
    registry
):
    if not tx:
        return 0

    now=time.time()

    seen=float(
        tx.get(
            "blockTime"
        )
        or now
    )

    slot=int(
        tx.get(
            "slot"
        )
        or 0
    )

    mints=mriya.tx_mints(
        tx
    )

    touched=0

    tokens=registry.setdefault(
        "tokens",
        {}
    )

    for mint in mints:

        if mint==WSOL:
            continue

        row=tokens.setdefault(
            mint,
            {
                "first_seen_epoch":
                    seen,

                "last_seen_epoch":
                    seen,

                "touches":
                    0,

                "last_slot":
                    0,

                "signatures":
                    [],

                "sources":
                    [],
            }
        )

        row[
            "first_seen_epoch"
        ]=min(
            float(
                row.get(
                    "first_seen_epoch",
                    seen
                )
            ),
            seen
        )

        row[
            "last_seen_epoch"
        ]=max(
            float(
                row.get(
                    "last_seen_epoch",
                    0
                )
            ),
            seen
        )

        row[
            "touches"
        ]=int(
            row.get(
                "touches",
                0
            )
        )+1

        row[
            "last_slot"
        ]=max(
            int(
                row.get(
                    "last_slot",
                    0
                )
            ),
            slot
        )

        sources=row.setdefault(
            "sources",
            []
        )

        if "PUMPSWAP_PROGRAM" not in sources:
            sources.append(
                "PUMPSWAP_PROGRAM"
            )

        sigs=row.setdefault(
            "signatures",
            []
        )

        if signature not in sigs:
            sigs.insert(
                0,
                signature
            )

            del sigs[8:]

        touched+=1

    return touched


async def fetch(
    signature
):
    return await mriya.rpc_retry(
        "getTransaction",
        [
            signature,
            {
                "encoding":
                    "jsonParsed",

                "commitment":
                    "confirmed",

                "maxSupportedTransactionVersion":
                    0,
            }
        ]
    )


async def consumer(
    queue,
    stop_at
):
    processed=0

    while (
        stop_at is None
        or time.monotonic()<stop_at
        or not queue.empty()
    ):

        try:
            signature=await asyncio.wait_for(
                queue.get(),
                timeout=.5
            )

        except asyncio.TimeoutError:
            continue

        data=load()

        done=set(
            data.get(
                "signatures"
            )
            or []
        )

        if signature in done:
            queue.task_done()
            continue

        try:
            tx=await fetch(
                signature
            )

            touched=ingest(
                signature,
                tx,
                data
            )

            sigs=data.setdefault(
                "signatures",
                []
            )

            sigs.append(
                signature
            )

            data[
                "signatures"
            ]=sigs[-1000:]

            data[
                "updated_epoch"
            ]=time.time()

            save(
                data
            )

            processed+=1

            print(
                "[PUMP_DISCOVERY_TX] "
                "sig=%s "
                "touched=%d "
                "registry=%d "
                "queue=%d"%(
                    signature[:16],
                    touched,
                    len(
                        data.get(
                            "tokens"
                        )
                        or {}
                    ),
                    queue.qsize()
                ),
                flush=True
            )

        except Exception as exc:

            print(
                "[PUMP_DISCOVERY_RETRY] "
                "sig=%s %s:%s"%(
                    signature[:16],
                    type(exc).__name__,
                    str(exc)[:120]
                ),
                flush=True
            )

        finally:
            queue.task_done()

    return processed


async def serve(
    seconds=None
):
    print(
        "[ORACLE-013] "
        "PUMPSWAP PROGRAM DISCOVERY",
        flush=True
    )

    print(
        "[SOURCE] program=%s"%PUMP,
        flush=True
    )

    print(
        "[MODE] READ_ONLY=True "
        "execution_authority=FALSE",
        flush=True
    )

    ws_url=(
        os.getenv(
            "SOLANA_WS_URL",
            ""
        ).strip()
        or c.RPC.replace(
            "https://",
            "wss://",
            1
        ).replace(
            "http://",
            "ws://",
            1
        )
    )

    started=time.monotonic()

    stop_at=(
        None
        if seconds is None
        else started+float(
            seconds
        )
    )

    queue=asyncio.Queue(
        maxsize=QUEUE_MAX
    )

    worker=asyncio.create_task(
        consumer(
            queue,
            stop_at
        )
    )

    reconnect=2.0

    try:

        while (
            stop_at is None
            or time.monotonic()<stop_at
        ):

            try:

                async with websockets.connect(
                    ws_url,
                    ping_interval=20,
                    ping_timeout=20,
                    max_size=4_000_000
                ) as ws:

                    await ws.send(
                        json.dumps({
                            "jsonrpc":"2.0",
                            "id":13,
                            "method":"logsSubscribe",
                            "params":[
                                {
                                    "mentions":[
                                        PUMP
                                    ]
                                },
                                {
                                    "commitment":
                                        "confirmed"
                                }
                            ]
                        })
                    )

                    reply=json.loads(
                        await ws.recv()
                    )

                    print(
                        "[PUMP_WS_SUBSCRIBED] %s"%(
                            reply.get(
                                "result"
                            )
                        ),
                        flush=True
                    )

                    reconnect=2.0

                    while (
                        stop_at is None
                        or time.monotonic()<stop_at
                    ):

                        try:
                            raw=await asyncio.wait_for(
                                ws.recv(),
                                timeout=1.0
                            )

                        except asyncio.TimeoutError:
                            continue

                        msg=json.loads(
                            raw
                        )

                        if (
                            msg.get(
                                "method"
                            )
                            !="logsNotification"
                        ):
                            continue

                        signature=(
                            (
                                (
                                    msg.get(
                                        "params"
                                    )
                                    or {}
                                ).get(
                                    "result"
                                )
                                or {}
                            ).get(
                                "value"
                            )
                            or {}
                        ).get(
                            "signature"
                        )

                        if not signature:
                            continue

                        try:
                            queue.put_nowait(
                                signature
                            )

                        except asyncio.QueueFull:
                            print(
                                "[PUMP_DISCOVERY_QUEUE_FULL]",
                                flush=True
                            )

            except Exception as exc:

                print(
                    "[PUMP_DISCOVERY_RECONNECT] "
                    "%s:%s sleep=%.1fs"%(
                        type(exc).__name__,
                        str(exc)[:100],
                        reconnect
                    ),
                    flush=True
                )

                await asyncio.sleep(
                    reconnect
                )

                reconnect=min(
                    reconnect*2.0,
                    10.0
                )

    finally:

        if stop_at is not None:

            try:
                await asyncio.wait_for(
                    queue.join(),
                    timeout=10
                )

            except Exception:
                pass

        worker.cancel()

        await asyncio.gather(
            worker,
            return_exceptions=True
        )


def main(argv=None):
    import argparse

    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=None
    )

    args=ap.parse_args(
        argv
    )

    asyncio.run(
        serve(
            args.seconds
        )
    )


if __name__=="__main__":
    main()
