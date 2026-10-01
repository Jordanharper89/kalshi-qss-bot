from pathlib import Path
import py_compile

ROOT=Path.cwd()

EXEC=ROOT/"qseries_v2/oracle_execution"
ENGINE=EXEC/"oracle_003_unified_physical_execution_engine.py"

DISC=EXEC/"oracle_013_pumpswap_program_discovery.py"
RUNNER=ROOT/"run_oracle_013_pumpswap_program_discovery.py"
TEST=ROOT/"test_oracle_013_broad_pumpswap_market_discovery.py"

if not ENGINE.is_file():
    raise SystemExit(
        "[FAIL] Oracle physical engine missing"
    )


# ============================================================
# ORACLE-013 SECOND DISCOVERY SOURCE
#
# Mriya remains source #1.
# PumpSwap program traffic becomes source #2.
#
# Discovery NEVER equals execution admission.
# Every token still must pass exact Pump/Meteora binding.
# ============================================================

DISC.write_text(
r'''
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
'''.strip()+"\n",
    encoding="utf-8"
)


RUNNER.write_text(
r'''
from qseries_v2.oracle_execution.oracle_013_pumpswap_program_discovery import (
    main
)

if __name__=="__main__":
    main()
'''.strip()+"\n",
    encoding="utf-8"
)


py_compile.compile(
    str(DISC),
    doraise=True
)

py_compile.compile(
    str(RUNNER),
    doraise=True
)


# ============================================================
# PATCH ORACLE ENGINE
#
# Add Pump discovery child beside Mriya.
# Merge discovery registries IN MEMORY.
#
# q45/q44 exact binding still decides whether a discovered
# token is a real PumpSwap <-> Meteora candidate.
# ============================================================

src=ENGINE.read_text(
    encoding="utf-8"
)


# Import broad discovery module.
needle='''from pathlib import Path
'''

replacement='''from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_013_pumpswap_program_discovery
    as oracle013_discovery
)
'''

if (
    "oracle_013_pumpswap_program_discovery"
    not in src
):

    if needle not in src:
        raise SystemExit(
            "[FAIL] engine Path import seam missing"
        )

    src=src.replace(
        needle,
        replacement,
        1
    )


# ------------------------------------------------------------
# Add second child global.
# ------------------------------------------------------------

needle2='''_DISCOVERY_CHILD=None
'''

replacement2='''_DISCOVERY_CHILD=None
_BROAD_DISCOVERY_CHILD=None
'''

if (
    "_BROAD_DISCOVERY_CHILD"
    not in src
):

    if needle2 not in src:
        raise SystemExit(
            "[FAIL] discovery child seam missing"
        )

    src=src.replace(
        needle2,
        replacement2,
        1
    )


# ------------------------------------------------------------
# Add broad child lifecycle + merged registry.
# Insert immediately before _stop_oracle_discovery().
# ------------------------------------------------------------

marker='''def _stop_oracle_discovery():
'''

insert=r'''
def _ensure_broad_discovery(
    root,
    seconds=150.0
):
    import subprocess
    import sys

    global _BROAD_DISCOVERY_CHILD

    if (
        _BROAD_DISCOVERY_CHILD is not None
        and _BROAD_DISCOVERY_CHILD.poll() is None
    ):
        return _BROAD_DISCOVERY_CHILD

    _BROAD_DISCOVERY_CHILD=subprocess.Popen(
        [
            sys.executable,
            "run_oracle_013_pumpswap_program_discovery.py",
            "--seconds",
            str(
                max(
                    30.0,
                    float(
                        seconds
                    )
                )
            )
        ],

        cwd=str(
            Path(
                root
            )
        ),

        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return _BROAD_DISCOVERY_CHILD


def _stop_broad_discovery():
    global _BROAD_DISCOVERY_CHILD

    child=_BROAD_DISCOVERY_CHILD
    _BROAD_DISCOVERY_CHILD=None

    if child is None:
        return

    try:

        if child.poll() is None:

            child.terminate()

            child.wait(
                timeout=5
            )

    except Exception:

        try:
            child.kill()

        except Exception:
            pass


def _merged_discovery_registry():
    primary=(
        q80.q45.d.load()
    )

    broad=(
        oracle013_discovery.load()
    )

    merged={
        "tokens":{},
        "signatures":[],
        "updated_epoch":
            max(
                float(
                    primary.get(
                        "updated_epoch",
                        0
                    )
                    or 0
                ),
                float(
                    broad.get(
                        "updated_epoch",
                        0
                    )
                    or 0
                ),
            ),
    }

    for source_name,data in (
        (
            "MRIYA",
            primary
        ),
        (
            "PUMPSWAP_PROGRAM",
            broad
        ),
    ):

        for token,info in (
            data.get(
                "tokens"
            )
            or {}
        ).items():

            existing=(
                merged[
                    "tokens"
                ].get(
                    token
                )
            )

            if existing is None:

                existing=dict(
                    info
                )

                existing[
                    "sources"
                ]=list(
                    dict.fromkeys(
                        list(
                            info.get(
                                "sources"
                            )
                            or []
                        )
                        +[
                            source_name
                        ]
                    )
                )

                merged[
                    "tokens"
                ][
                    token
                ]=existing

                continue


            existing[
                "first_seen_epoch"
            ]=min(
                float(
                    existing.get(
                        "first_seen_epoch",
                        1e30
                    )
                ),
                float(
                    info.get(
                        "first_seen_epoch",
                        1e30
                    )
                )
            )

            existing[
                "last_seen_epoch"
            ]=max(
                float(
                    existing.get(
                        "last_seen_epoch",
                        0
                    )
                ),
                float(
                    info.get(
                        "last_seen_epoch",
                        0
                    )
                )
            )

            existing[
                "touches"
            ]=(
                int(
                    existing.get(
                        "touches",
                        0
                    )
                )
                +int(
                    info.get(
                        "touches",
                        0
                    )
                )
            )

            existing[
                "last_slot"
            ]=max(
                int(
                    existing.get(
                        "last_slot",
                        0
                    )
                ),
                int(
                    info.get(
                        "last_slot",
                        0
                    )
                )
            )

            existing[
                "sources"
            ]=list(
                dict.fromkeys(
                    list(
                        existing.get(
                            "sources"
                        )
                        or []
                    )
                    +list(
                        info.get(
                            "sources"
                        )
                        or []
                    )
                    +[
                        source_name
                    ]
                )
            )

    return merged


def _classify_merged_discovery():
    merged=(
        _merged_discovery_registry()
    )

    discovery_module=(
        q80.q45.d
    )

    original_load=(
        discovery_module.load
    )

    discovery_module.load=(
        lambda:
            merged
    )

    try:

        return (
            q80.q45.classify()
        )

    finally:

        discovery_module.load=(
            original_load
        )


def _recent_oracle_tokens(
    hot_seconds
):
    reg=(
        _merged_discovery_registry()
    )

    now=time.time()

    rows=[]

    for token,info in (
        reg.get(
            "tokens"
        )
        or {}
    ).items():

        age=max(
            0.0,
            now-float(
                info.get(
                    "last_seen_epoch",
                    0
                )
                or 0
            )
        )

        if age<=hot_seconds:

            rows.append(
                (
                    token,
                    age,
                    tuple(
                        info.get(
                            "sources"
                        )
                        or []
                    )
                )
            )

    rows.sort(
        key=lambda x:
            x[1]
    )

    return rows


'''

if (
    "def _merged_discovery_registry("
    not in src
):

    if marker not in src:
        raise SystemExit(
            "[FAIL] stop discovery seam missing"
        )

    src=src.replace(
        marker,
        insert+marker,
        1
    )


# ------------------------------------------------------------
# Ensure Mriya launcher ALSO starts broad Pump discovery.
# ------------------------------------------------------------

old_return='''    return _DISCOVERY_CHILD


def _stop_oracle_discovery():
'''

new_return='''    _ensure_broad_discovery(
        root,
        seconds
    )

    return _DISCOVERY_CHILD


def _stop_oracle_discovery():
'''

if old_return in src:

    src=src.replace(
        old_return,
        new_return,
        1
    )


# ------------------------------------------------------------
# Stop both children.
# ------------------------------------------------------------

old_stop='''    global _DISCOVERY_CHILD

    child=_DISCOVERY_CHILD
'''

new_stop='''    global _DISCOVERY_CHILD

    _stop_broad_discovery()

    child=_DISCOVERY_CHILD
'''

if (
    "_stop_broad_discovery()\n\n    child=_DISCOVERY_CHILD"
    not in src
):

    if old_stop not in src:
        raise SystemExit(
            "[FAIL] stop-child body seam missing"
        )

    src=src.replace(
        old_stop,
        new_stop,
        1
    )


# ------------------------------------------------------------
# Convert the old Mriya-only recent-token reader into merged
# Oracle discovery.
# ------------------------------------------------------------

start=src.find(
    "def _recent_mriya_count(\n"
)

end=src.find(
    "\n\ndef refresh_live_universe_rows(",
    start
)

if (
    start>=0
    and end>=0
):

    src=(
        src[:start]
        +'''def _recent_mriya_count(
    hot_seconds
):
    # Compatibility name retained.
    # Source is now MRIYA + PUMPSWAP_PROGRAM.
    return [
        (
            token,
            age
        )
        for token,age,sources
        in _recent_oracle_tokens(
            hot_seconds
        )
    ]
'''
        +src[end:]
    )


# ------------------------------------------------------------
# q45.classify() -> merged discovery classify.
# Only change calls inside refresh/live discovery paths.
# ------------------------------------------------------------

refresh_start=src.find(
    "def refresh_live_universe_rows(\n"
)

refresh_end=src.find(
    "\n\ndef live_universe_rows(",
    refresh_start
)

if (
    refresh_start<0
    or refresh_end<0
):
    raise SystemExit(
        "[FAIL] refresh universe seam missing"
    )

chunk=src[
    refresh_start:
    refresh_end
]

chunk=chunk.replace(
    "q80.q45.classify()",
    "_classify_merged_discovery()"
)

src=(
    src[:refresh_start]
    +chunk
    +src[refresh_end:]
)


# Update user-visible source labels.
src=src.replace(
    "source=MRIYA ",
    "source=MRIYA+PUMPSWAP_PROGRAM "
)

src=src.replace(
    "recent_mriya=",
    "recent_discovery="
)


ENGINE.write_text(
    src,
    encoding="utf-8"
)

py_compile.compile(
    str(ENGINE),
    doraise=True
)


# ============================================================
# TEST
# ============================================================

TEST.write_text(
r'''
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as e
)

from qseries_v2.oracle_execution import (
    oracle_013_pumpswap_program_discovery
    as d
)


class T(unittest.TestCase):

    def test_discovery_read_only(self):

        self.assertFalse(
            d.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            d.READ_ONLY
        )


    def test_pump_program_source(self):

        self.assertEqual(
            d.PUMP,
            e.base.q87.c.PUMP
        )


    def test_separate_registry(self):

        self.assertIn(
            "oracle_013_pumpswap_program_tokens.json",
            str(
                d.STATE
            )
        )


    def test_mriya_preserved(self):

        s=inspect.getsource(
            e._ensure_oracle_discovery
        )

        self.assertIn(
            "run_qarb_043b_paced_mriya_token_discovery.py",
            s
        )


    def test_broad_discovery_added(self):

        s=inspect.getsource(
            e._ensure_broad_discovery
        )

        self.assertIn(
            "run_oracle_013_pumpswap_program_discovery.py",
            s
        )


    def test_registry_merge(self):

        s=inspect.getsource(
            e._merged_discovery_registry
        )

        self.assertIn(
            "MRIYA",
            s
        )

        self.assertIn(
            "PUMPSWAP_PROGRAM",
            s
        )


    def test_exact_binding_still_required(self):

        s=inspect.getsource(
            e.refresh_live_universe_rows
        )

        self.assertIn(
            "_classify_merged_discovery",
            s
        )

        self.assertIn(
            "pump_pool",
            s
        )

        self.assertIn(
            "meteora_meta",
            s
        )


    def test_no_stale_memory_fallback(self):

        s=inspect.getsource(
            e.refresh_live_universe_rows
        )

        self.assertNotIn(
            "q80.select_rows",
            s
        )

        self.assertNotIn(
            "q80.MEMORY",
            s
        )


    def test_discovery_has_no_execution(self):

        with open(
            d.__file__,
            encoding="utf-8"
        ) as f:
            s=f.read()

        self.assertNotIn(
            "sendTransaction",
            s
        )

        self.assertNotIn(
            "send_once(",
            s
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
'''.strip()+"\n",
    encoding="utf-8"
)

py_compile.compile(
    str(TEST),
    doraise=True
)


print(
    "[PASS] ORACLE-013 broad PumpSwap market discovery installed"
)

print(
    "[SOURCE_1] Mriya discovery preserved"
)

print(
    "[SOURCE_2] direct PumpSwap program activity"
)

print(
    "[REGISTRY] sources remain physically separate; merged in memory"
)

print(
    "[ADMISSION] exact PumpSwap + Meteora binding remains mandatory"
)

print(
    "[FRESHNESS] execution candidates remain HOT <=90s"
)

print(
    "[STALE_MEMORY] prohibited from execution intake"
)

print(
    "[PRICING] official physical bidirectional scanner unchanged"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[OWNER] ORACLE"
)