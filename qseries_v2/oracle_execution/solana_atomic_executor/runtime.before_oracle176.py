from __future__ import annotations
# ORACLE162_SIGNATURE_BOUNDARY_IMPORT
from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle162_exact_signature_boundary import verify_and_sign as _oracle162_verify_and_sign

import argparse
import asyncio
import base64
import copy
import json
import os
import struct
import threading
import time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_018_exact_sdk_hot_lane_cutover as q18
)

from qseries_v2.oracle_execution import (
    oracle_020_latest_state_exact_pricing_worker as q20
)

from qseries_v2.oracle_execution import (
    oracle_025_single_hydration_exact_live_reuse as q25
)

from qseries_v2.oracle_execution.solana_atomic_executor import mry_001_continuous_replenishment as mry1
from qseries_v2.oracle_execution.solana_atomic_executor import mry_002_warm_inventory as mry2
from qseries_v2.oracle_execution.solana_atomic_executor import mry_005_runtime_activation as mry5
from qseries_v2.oracle_execution.solana_atomic_executor import mry_014_alt_preload_resilience as m14

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair as q87
)

from qseries_v2.solana_live_execution import (
    qarb_096_sequential_live_micro_executor as q96
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

MAX_TX_BYTES=1232

FAST_SIZES=(0.050,)

EXPAND_SIZES=()

EXPAND_GATE_BPS=-100.0

BUY_DISC=bytes([
    102,6,61,18,1,218,235,234
])

BUY_EXACT_QUOTE_IN_DISC=bytes([
    198,46,21,82,180,217,232,112
])

persistent=q25.q19.persistent

USER=None
TEMPLATES={}
METEORA_TEMPLATES={}
READY_TOKENS=set()


class BlockhashCache:

    def __init__(self):
        self.lock=threading.Lock()
        self.value=None
        self.updated=0.0
        self.stop=False
        self.thread=None

    def refresh(self):
        x=q87.c.rpc(
            "getLatestBlockhash",
            [{
                "commitment":"processed"
            }]
        )

        if (
            not isinstance(x,dict)
            or not isinstance(
                x.get("value"),
                dict
            )
            or not x["value"].get(
                "blockhash"
            )
        ):
            raise RuntimeError(
                "BAD_BLOCKHASH_RESPONSE"
            )

        with self.lock:
            self.value=x[
                "value"
            ][
                "blockhash"
            ]

            self.updated=time.monotonic()

        return self.value

    def get(self):
        with self.lock:
            value=self.value
            age=(
                time.monotonic()
                -self.updated
            )

        if (
            value is None
            or age>45.0
        ):
            return self.refresh()

        return value

    def _loop(self):
        while not self.stop:

            try:
                self.refresh()

            except Exception as exc:
                print(
                    "[CANONICAL_BLOCKHASH_WARN] "
                    "%s:%s"
                    %(
                        type(exc).__name__,
                        str(exc)[:200],
                    ),
                    flush=True,
                )

            for _ in range(100):

                if self.stop:
                    return

                time.sleep(.1)

    def start(self):
        for _attempt in range(1,7):
            try:
                self.refresh()
                break
            except Exception as _exc:
                if _attempt>=6:
                    raise
                print(
                    "[SAE008C_BLOCKHASH_RETRY] attempt=%d error=%s:%s"%(
                        _attempt,
                        type(_exc).__name__,
                        _exc,
                    ),
                    flush=True,
                )
                time.sleep(min(0.5*_attempt,2.0))

        self.thread=threading.Thread(
            target=self._loop,
            name="canonical-blockhash",
            daemon=True,
        )

        self.thread.start()

    def close(self):
        self.stop=True

        if self.thread:
            self.thread.join(
                timeout=2
            )


BLOCKHASH=BlockhashCache()


def immutable_snapshot(pair):
    return {
        "token":
            str(pair.token),

        "pump_pool":
            str(pair.pump_pool),

        "meteora":{
            "address":
                str(
                    pair.meteora_pool
                ),

            "token_x":
                str(pair.token_x),

            "token_y":
                str(pair.token_y),

            "decimals_x":
                int(
                    pair.decimals_x
                ),

            "decimals_y":
                int(
                    pair.decimals_y
                ),
        },

        "dlmm_state":
            copy.deepcopy(
                pair.dlmm_state
            ),

        "pump_base_reserve":
            int(
                pair.pump_base_reserve
            ),

        "pump_quote_reserve":
            int(
                pair.pump_quote_reserve
            ),
    }


def pump_ix_position(ixs):

    rows=[
        i
        for i,x in enumerate(ixs)
        if x.get(
            "programId"
        )==q87.c.PUMP
    ]

    if len(rows)!=1:
        raise RuntimeError(
            "PUMP_PROGRAM_IX_COUNT:"
            +str(len(rows))
        )

    return rows[0]


def rewrite_pump_buy_bounds(
    ix,
    spendable_quote,
    min_base_out
):
    #
    # PumpSwap execution semantics:
    #
    # BUY_EXACT_QUOTE_IN:
    #
    #   spendableQuoteIn
    #   minBaseAmountOut
    #
    # Fees are deducted from the fixed
    # spendable quote budget by PumpSwap.
    #
    # This is the correct instruction for
    # Oracle's PUMP_TO_METEORA pricing:
    #
    #   "spend exactly X SOL"
    #        ->
    #   "receive at least Y tokens"
    #
    # Do NOT convert this into BUY
    # (baseAmountOut/maxQuoteAmountIn).
    #
    out=dict(ix)

    raw=bytearray(
        base64.b64decode(
            out.get("data")
            or ""
        )
    )

    if len(raw)<24:
        raise RuntimeError(
            "PUMP_IX_DATA_TOO_SHORT:"
            +str(len(raw))
        )

    original_disc=bytes(
        raw[:8]
    )

    if original_disc not in (
        BUY_DISC,
        BUY_EXACT_QUOTE_IN_DISC,
    ):
        raise RuntimeError(
            "PUMP_TEMPLATE_NOT_BUY_FAMILY:"
            +original_disc.hex()
        )

    #
    # Force the correct fixed-budget
    # instruction discriminator.
    #
    raw[:8]=(
        BUY_EXACT_QUOTE_IN_DISC
    )

    #
    # ARG 1:
    # spendable_quote_in
    #
    raw[8:16]=struct.pack(
        "<Q",
        int(
            spendable_quote
        ),
    )

    #
    # ARG 2:
    # min_base_amount_out
    #
    # We deliberately use the exact
    # same-snapshot gross Pump output,
    # not a looser value.
    #
    # If the pool moves against Oracle,
    # the atomic transaction must fail
    # instead of consuming a worse fill.
    #
    raw[16:24]=struct.pack(
        "<Q",
        int(
            min_base_out
        ),
    )

    #
    # Preserve the SDK-produced trailing
    # trackVolume / OptionBool encoding.
    #
    out["data"]=base64.b64encode(
        bytes(raw)
    ).decode()

    return out



def prebuild_templates(
    state,
    user
):
    global TEMPLATES
    global READY_TOKENS

    TEMPLATES={}
    READY_TOKENS=set()

    for pair in list(
        state.get("pairs")
        or []
    ):
        token=str(pair.token)
        pool=str(pair.pump_pool)
        last=None

        for attempt in range(1,4):
            try:
                ixs,_=(
                    q87.las.q59
                    .native_pump_buy_ixs(
                        user,
                        pool,
                        CANARY_TRADE_LAMPORTS,
                    )
                )

                pos=pump_ix_position(ixs)

                TEMPLATES[token]={
                    "pump_pool":pool,
                    "instructions":[
                        copy.deepcopy(x)
                        for x in ixs
                    ],
                    "pump_index":int(pos),
                    "template_quote_lamports":
                        int(CANARY_TRADE_LAMPORTS),
                }

                READY_TOKENS.add(token)

                print(
                    "[CANONICAL_TEMPLATE_READY] "
                    "token=%s pump=%s "
                    "instructions=%d "
                    "quote_lamports=%d "
                    "exact_size=0.010 "
                    "attempt=%d"
                    %(
                        token[:10],
                        pool[:12],
                        len(ixs),
                        CANARY_TRADE_LAMPORTS,
                        attempt,
                    ),
                    flush=True,
                )
                break

            except Exception as exc:
                last=exc
                print(
                    "[CANONICAL_TEMPLATE_RETRY] "
                    "token=%s attempt=%d %s:%s"
                    %(
                        token[:10],
                        attempt,
                        type(exc).__name__,
                        str(exc)[:240],
                    ),
                    flush=True,
                )
                time.sleep(.4*attempt)

        if token not in READY_TOKENS:
            print(
                "[CANONICAL_TEMPLATE_HOLD] "
                "token=%s reason=%s:%s"
                %(
                    token[:10],
                    type(last).__name__
                    if last else "UNKNOWN",
                    str(last)[:240]
                    if last else "",
                ),
                flush=True,
            )

    if not READY_TOKENS:
        raise RuntimeError(
            "NO_CANONICAL_PUMP_TEMPLATES"
        )

    return len(READY_TOKENS)




def prebuild_meteora_templates(
    state,
    user,
    warmed_rows
):
    global METEORA_TEMPLATES
    global READY_TOKENS

    METEORA_TEMPLATES={}

    programs={
        str(row["token"]):
            str(row["program"])
        for row in (
            warmed_rows
            or []
        )
        if (
            row.get("token")
            and row.get("program")
        )
    }

    programs[
        q87.c.WSOL
    ]=q87.c.TOKEN

    descriptors=[]

    for pair in list(
        state.get("pairs")
        or []
    ):
        token=str(
            pair.token
        )

        if token not in READY_TOKENS:
            continue

        pool=str(
            pair.meteora_pool
        )

        token_x=str(
            pair.token_x
        )

        token_y=str(
            pair.token_y
        )

        tx_prog=programs.get(
            token_x
        )

        ty_prog=programs.get(
            token_y
        )

        if (
            not tx_prog
            or not ty_prog
        ):
            print(
                "[SAE001_HOLD] "
                "token=%s "
                "reason=TOKEN_PROGRAM_NOT_PREWARMED "
                "x=%s y=%s"
                %(
                    token[:10],
                    str(tx_prog),
                    str(ty_prog),
                ),
                flush=True,
            )
            continue

        ux=q87.c.ata(
            user,
            token_x,
            tx_prog,
        )

        uy=q87.c.ata(
            user,
            token_y,
            ty_prog,
        )

        rx=q87.c.pda(
            [
                q87.c.b58d(pool),
                q87.c.b58d(token_x),
            ],
            q87.c.DLMM,
        )

        ry=q87.c.pda(
            [
                q87.c.b58d(pool),
                q87.c.b58d(token_y),
            ],
            q87.c.DLMM,
        )

        oracle=q87.c.pda(
            [
                b"oracle",
                q87.c.b58d(pool),
            ],
            q87.c.DLMM,
        )

        bitmap=q87.c.pda(
            [
                b"bitmap",
                q87.c.b58d(pool),
            ],
            q87.c.DLMM,
        )

        event_authority=q87.c.pda(
            [
                b"__event_authority"
            ],
            q87.c.DLMM,
        )

        arrays=[
            (
                int(a[0]),
                str(a[1]),
            )
            for a in list(
                pair.arrays
            )
        ]

        arrays.sort(
            key=lambda x:x[0]
        )

        if not arrays:
            print(
                "[SAE001_HOLD] "
                "token=%s "
                "reason=NO_PREWARMED_DLMM_ARRAYS"
                %token[:10],
                flush=True,
            )
            continue

        if token_x==q87.c.WSOL:
            source=uy
            dest=ux
            swap_for_y=False

        elif token_y==q87.c.WSOL:
            source=ux
            dest=uy
            swap_for_y=True

        else:
            print(
                "[SAE001_HOLD] "
                "token=%s "
                "reason=DLMM_PAIR_NOT_WSOL"
                %token[:10],
                flush=True,
            )
            continue

        descriptors.append({
            "token":token,
            "pool":pool,
            "token_x":token_x,
            "token_y":token_y,
            "tx_prog":tx_prog,
            "ty_prog":ty_prog,
            "ux":ux,
            "uy":uy,
            "rx":rx,
            "ry":ry,
            "oracle":oracle,
            "bitmap":bitmap,
            "event_authority":
                event_authority,
            "source":source,
            "dest":dest,
            "swap_for_y":
                bool(swap_for_y),
            "arrays":arrays,
        })

    if not descriptors:
        raise RuntimeError(
            "NO_METEORA_PREBUILD_DESCRIPTORS"
        )

    bitmap_addresses=[
        row["bitmap"]
        for row in descriptors
    ]

    bitmap_values=None
    last_error=None

    for attempt in range(1,6):
        try:
            result=q87.c.rpc(
                "getMultipleAccounts",
                [
                    bitmap_addresses,
                    {
                        "encoding":"base64",
                        "commitment":"processed",
                    },
                ],
            )

            if not isinstance(
                result,
                dict
            ):
                raise RuntimeError(
                    "BITMAP_BATCH_RESULT_NOT_MAPPING"
                )

            values=result.get(
                "value"
            )

            if not isinstance(
                values,
                list
            ):
                raise RuntimeError(
                    "BITMAP_BATCH_VALUE_NOT_LIST"
                )

            if len(values)!=len(
                bitmap_addresses
            ):
                raise RuntimeError(
                    "BITMAP_BATCH_LENGTH_MISMATCH"
                )

            bitmap_values=values
            break

        except Exception as exc:
            last_error=exc

            if "429" not in str(exc):
                raise

            delay=min(
                8.0,
                .75*(2**(attempt-1)),
            )

            print(
                "[SAE001_BITMAP_429] "
                "attempt=%d sleep=%.2fs"
                %(
                    attempt,
                    delay,
                ),
                flush=True,
            )

            time.sleep(delay)

    if bitmap_values is None:
        raise RuntimeError(
            "METEORA_BITMAP_BATCH_UNAVAILABLE:"
            +str(last_error)
        )

    for row,bitmap_account in zip(
        descriptors,
        bitmap_values,
    ):
        bitmap_key=(
            row["bitmap"]
            if bitmap_account
            else q87.c.DLMM
        )

        fixed_accounts=[
            (
                row["pool"],
                False,
                True,
            ),
            (
                bitmap_key,
                False,
                True,
            ),
            (
                row["rx"],
                False,
                True,
            ),
            (
                row["ry"],
                False,
                True,
            ),
            (
                row["source"],
                False,
                True,
            ),
            (
                row["dest"],
                False,
                True,
            ),
            (
                row["token_x"],
                False,
                False,
            ),
            (
                row["token_y"],
                False,
                False,
            ),
            (
                row["oracle"],
                False,
                True,
            ),
            (
                q87.c.DLMM,
                False,
                True,
            ),
            (
                user,
                True,
                False,
            ),
            (
                row["tx_prog"],
                False,
                False,
            ),
            (
                row["ty_prog"],
                False,
                False,
            ),
            (
                row["event_authority"],
                False,
                False,
            ),
            (
                q87.c.DLMM,
                False,
                False,
            ),
        ]

        token=row["token"]

        METEORA_TEMPLATES[token]={
            "pool":
                row["pool"],

            "token_x":
                row["token_x"],

            "token_y":
                row["token_y"],

            "swap_for_y":
                row["swap_for_y"],

            "arrays":
                list(row["arrays"]),

            "fixed_accounts":
                fixed_accounts,
        }

        print(
            "[SAE001_METEORA_READY] "
            "token=%s pool=%s "
            "arrays=%d bitmap=%s"
            %(
                token[:10],
                row["pool"][:12],
                len(row["arrays"]),
                (
                    "EXTENSION"
                    if bitmap_account
                    else "PROGRAM_SENTINEL"
                ),
            ),
            flush=True,
        )

    READY_TOKENS.intersection_update(
        set(METEORA_TEMPLATES)
    )

    if not READY_TOKENS:
        raise RuntimeError(
            "NO_FULLY_PREBUILT_EXECUTION_PAIRS"
        )

    return len(
        METEORA_TEMPLATES
    )



def build_meteora_ix_hot(token,input_amount,quote_result):
    template=METEORA_TEMPLATES.get(str(token))
    if template is None:
        raise RuntimeError("METEORA_TEMPLATE_MISSING:"+str(token))

    swap_for_y=bool(quote_result.get("swap_for_y"))
    if swap_for_y!=template["swap_for_y"]:
        raise RuntimeError("DLMM_QUOTE_DIRECTION_MISMATCH")

    arrays=list(template["arrays"])
    crossed=max(1,int(quote_result.get("bins_crossed") or 1))
    n=min(len(arrays),max(1,(crossed+69)//70))

    if swap_for_y:
        chosen=arrays[:n]
    else:
        chosen=list(reversed(arrays))[:n]

    fixed=list(template["fixed_accounts"])
    if len(fixed)!=15:
        raise RuntimeError("MRY034_LEGACY_FIXED_LAYOUT:"+str(len(fixed)))

    memo=(
        "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr",
        False,
        False,
    )

    accounts=fixed[:13]+[memo]+fixed[13:]

    accounts.extend(
        (address,False,True)
        for _,address in chosen
    )

    min_out=(
        int(quote_result["raw_out"])
        *(10000-q87.las.q59.SLIPPAGE_BPS)
        //10000
    )

    data=(
        bytes([65,75,63,76,235,91,91,136])
        +struct.pack("<QQ",int(input_amount),int(min_out))
        +struct.pack("<I",0)
    )

    if len(accounts)<=16:
        raise RuntimeError("MRY034_NO_BIN_ARRAY_ACCOUNTS")

    return {
        "programId":q87.c.DLMM,
        "accounts":[
            {
                "pubkey":pubkey,
                "isSigner":signer,
                "isWritable":writable,
            }
            for pubkey,signer,writable in accounts
        ],
        "data":base64.b64encode(data).decode(),
    }



def install_proven_hot_math(
    state
):

    warmed=(
        q25.install_hot_math_and_prewarm(
            state
        )
    )

    q18.install_exact_hot_math()

    return warmed



CANARY_TRADE_SOL=0.050
CANARY_TRADE_LAMPORTS=50_000_000
# ORACLE160_EXACT_AMOUNT_CONTRACT
if int(round(CANARY_TRADE_SOL * 1_000_000_000)) != CANARY_TRADE_LAMPORTS:
    raise RuntimeError("ORACLE160_CANARY_AMOUNT_MISMATCH")
FAST_010_ZERO_WAIT_COHERENCE=True
FAST_010_VERBOSE_TELEMETRY=False
COHERENCE_QUIET_NS=3_000_000
COHERENCE_MAX_HOLD_NS=12_000_000
COHERENCE_MIN_MUTATIONS=2
COHERENCE_MIN_KINDS=2
COHERENCE_PENDING={}


def _coherence_stage(token,snap,slot,received_ns,kind):
    now=time.perf_counter_ns()
    previous=COHERENCE_PENDING.get(token)

    if previous is None or int(slot)!=int(previous["slot"]):
        COHERENCE_PENDING[token]={
            "snap":snap,
            "slot":int(slot),
            "received_ns":int(received_ns),
            "first_ns":now,
            "last_ns":now,
            "mutations":1,
            "kinds":{str(kind)},
        }
        return

    previous["snap"]=snap
    previous["received_ns"]=int(received_ns)
    previous["last_ns"]=now
    previous["mutations"]=int(previous["mutations"])+1
    previous["kinds"].add(str(kind))


def _coherence_flush(
    lane,
    force=False,
):
    now=time.perf_counter_ns()

    for token,row in list(
        COHERENCE_PENDING.items()
    ):
        held_ns=(
            now-int(
                row["first_ns"]
            )
        )

        mutations=int(
            row["mutations"]
        )

        kinds=len(
            row["kinds"]
        )

        coherent=(
            mutations>=COHERENCE_MIN_MUTATIONS
            and kinds>=COHERENCE_MIN_KINDS
        )

        deadline=(
            held_ns>=COHERENCE_MAX_HOLD_NS
        )

        if not (
            coherent
            or deadline
            or force
        ):
            continue

        current=COHERENCE_PENDING.get(
            token
        )

        if current is not row:
            continue

        del COHERENCE_PENDING[
            token
        ]

        if not coherent:
            if FAST_010_VERBOSE_TELEMETRY:
                print(
                    "[COHERENCE_INCOMPLETE_HOLD] "
                    "token=%s slot=%s "
                    "mutations=%d kinds=%d held_ms=%.3f"
                    %(
                        token[:10],
                        row["slot"],
                        mutations,
                        kinds,
                        held_ns/1e6,
                    ),
                    flush=False,
                )
            continue

        lane.submit(
            token,
            row["snap"],
            row["slot"],
            row["received_ns"],
        )

        if FAST_010_VERBOSE_TELEMETRY:
            print(
                "[COHERENCE_RELEASE] "
                "token=%s slot=%s "
                "mutations=%d kinds=%d "
                "held_ms=%.3f immediate=TRUE"
                %(
                    token[:10],
                    row["slot"],
                    mutations,
                    kinds,
                    held_ns/1e6,
                ),
                flush=False,
            )






def exact_best(
    lane,
    token,
    snap,
    generation,
):
    rows=q18.exact_snapshot_opportunities(
        snap,
        CANARY_TRADE_SOL,
    )

    if not rows:
        raise RuntimeError(
            "SAE005E_NO_001_QUOTES"
        )

    return max(
        rows,
        key=lambda x:int(
            x["local_net"]
        ),
    )






SELL_TEMPLATES={}


def _pump_sell_template_live(user,pump_pool,base_amount):
    import json
    import os
    import shutil
    import subprocess

    node=shutil.which("node")

    if node is None:
        raise RuntimeError("REVERSE_PUMP_SELL_NODE_MISSING")

    helper=(
        Path.cwd()
        /"qseries_v2/oracle_strategy_intelligence/"
        "solana_money/qsb059d_pump_native/"
        "build_sell_ix.mjs"
    )

    if not helper.is_file():
        raise RuntimeError("REVERSE_PUMP_SELL_HELPER_MISSING")

    req={
        "rpc":os.getenv(
            "SOLANA_RPC_URL",
            "https://api.mainnet-beta.solana.com",
        ),
        "user":str(user),
        "pool":str(pump_pool),
        "baseAmount":int(base_amount),
        "slippagePct":0.20,
        "pumpProgram":q87.c.PUMP,
    }

    p=subprocess.run(
        [node,helper.name],
        cwd=str(helper.parent),
        input=json.dumps(req),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=45,
    )

    if p.returncode!=0:
        raise RuntimeError(
            "REVERSE_PUMP_SELL_NODE_FAILED:"
            +p.stderr[-1200:]
        )

    try:
        row=json.loads(p.stdout.strip().splitlines()[-1])
    except Exception as exc:
        raise RuntimeError(
            "REVERSE_PUMP_SELL_BAD_JSON:"
            +p.stdout[-1200:]
        ) from exc

    if not row.get("ok"):
        raise RuntimeError(
            "REVERSE_PUMP_SELL_BUILD_FAILED:"
            +str(row.get("reason"))
        )

    ixs=list(row.get("instructions") or [])
    pos=pump_ix_position(ixs)

    return {
        "pump_pool":str(pump_pool),
        "instructions":ixs,
        "pump_index":int(pos),
    }


def prebuild_sell_templates(state,user):
    SELL_TEMPLATES.clear()

    for pair in list(state.get("pairs") or []):
        token=str(pair.token)

        if token not in READY_TOKENS:
            continue

        try:
            snap=immutable_snapshot(pair)

            rows=q18.exact_snapshot_opportunities(
                snap,
                0.005,
            )

            reverse=next(
                x for x in rows
                if x.get("direction")=="METEORA_TO_PUMP"
            )

            amount=int(reverse["net_token"])

            if amount<=0:
                raise RuntimeError("REVERSE_TEMPLATE_AMOUNT_ZERO")

            SELL_TEMPLATES[token]=_pump_sell_template_live(
                user,
                pair.pump_pool,
                amount,
            )

            print(
                "[REVERSE_005_SELL_TEMPLATE_READY] "
                "token=%s pump=%s"
                %(token[:10],str(pair.pump_pool)[:12]),
                flush=True,
            )

        except Exception as exc:
            print(
                "[REVERSE_005_SELL_TEMPLATE_HOLD] "
                "token=%s %s:%s"
                %(token[:10],type(exc).__name__,str(exc)[:220]),
                flush=True,
            )

    return len(SELL_TEMPLATES)


def rewrite_pump_sell_bounds(ix,base_in,min_quote_out):
    out=copy.deepcopy(ix)

    raw=bytearray(
        base64.b64decode(out.get("data") or "")
    )

    if len(raw)<24:
        raise RuntimeError(
            "REVERSE_PUMP_SELL_DATA_TOO_SHORT:"+str(len(raw))
        )

    raw[8:16]=struct.pack("<Q",int(base_in))
    raw[16:24]=struct.pack("<Q",int(min_quote_out))

    out["data"]=base64.b64encode(bytes(raw)).decode()

    return out


def build_meteora_buy_ix_hot(token,input_lamports,quote_result):
    template=METEORA_TEMPLATES.get(str(token))

    if template is None:
        raise RuntimeError(
            "REVERSE_METEORA_TEMPLATE_MISSING:"+str(token)
        )

    swap_for_y=bool(quote_result.get("swap_for_y"))

    if swap_for_y==bool(template["swap_for_y"]):
        raise RuntimeError("REVERSE_DLMM_DIRECTION_NOT_OPPOSITE")

    arrays=list(template["arrays"])
    crossed=max(1,int(quote_result.get("bins_crossed") or 1))
    n=min(len(arrays),max(1,(crossed+69)//70))

    chosen=(
        arrays[:n]
        if swap_for_y
        else list(reversed(arrays))[:n]
    )

    accounts=[tuple(x) for x in template["fixed_accounts"]]

    if len(accounts)<6:
        raise RuntimeError("REVERSE_METEORA_FIXED_ACCOUNTS_SHORT")

    accounts[4],accounts[5]=accounts[5],accounts[4]

    accounts.extend(
        (address,False,True)
        for _,address in chosen
    )

    min_out=(
        int(quote_result["raw_out"])
        *(10000-q87.las.q59.SLIPPAGE_BPS)
        //10000
    )

    data=(
        bytes([248,198,158,145,225,117,135,200])
        +struct.pack("<QQ",int(input_lamports),int(min_out))
    )

    return {
        "programId":q87.c.DLMM,
        "accounts":[
            {
                "pubkey":p,
                "isSigner":s,
                "isWritable":w,
            }
            for p,s,w in accounts
        ],
        "data":base64.b64encode(data).decode(),
    }


def _reverse_instruction_sets(sell_ixs,pump_index,meteora_ix):
    pre=list(sell_ixs[:pump_index])
    pump=sell_ixs[pump_index]
    post=list(sell_ixs[pump_index+1:])

    full=pre+[meteora_ix,pump]+post

    compact=[
        x for x in pre
        if (
            x.get("programId") not in q87.las.q59.MEMO_PROGRAMS
            and x.get("programId")!=q87.las.q59.COMPUTE_BUDGET
        )
    ]

    compact += [meteora_ix,pump]

    compact += [
        x for x in post
        if (
            x.get("programId") not in q87.las.q59.MEMO_PROGRAMS
            and x.get("programId")!=q87.las.q59.COMPUTE_BUDGET
        )
    ]

    return [
        ("REVERSE_FULL",full),
        ("REVERSE_NO_COMPUTE_MEMO",compact),
    ]


def same_snapshot_reverse_route(user,snap,opportunity):
    token=str(snap["token"])
    template=SELL_TEMPLATES.get(token)

    if template is None:
        raise RuntimeError(
            "REVERSE_SELL_TEMPLATE_MISSING:"+token
        )

    if template["pump_pool"]!=snap["pump_pool"]:
        raise RuntimeError("REVERSE_PUMP_TEMPLATE_BINDING_DRIFT")

    start=int(opportunity["start"])
    base_in=int(opportunity["net_token"])
    min_quote=int(opportunity["local_min_end"])

    if start!=CANARY_TRADE_LAMPORTS or base_in<=0 or min_quote<=0:
        raise RuntimeError("REVERSE_005_BAD_EXECUTION_BOUND")

    sell_ixs=[
        copy.deepcopy(x)
        for x in template["instructions"]
    ]

    pump_index=int(template["pump_index"])

    sell_ixs[pump_index]=rewrite_pump_sell_bounds(
        sell_ixs[pump_index],
        base_in,
        min_quote,
    )

    pump_ix=sell_ixs[pump_index]

    if not any(
        a.get("pubkey")==snap["pump_pool"]
        for a in (pump_ix.get("accounts") or [])
    ):
        raise RuntimeError("REVERSE_PUMP_POOL_ACCOUNT_DRIFT")

    meteora_ix=build_meteora_buy_ix_hot(
        token,
        start,
        dict(opportunity["mq"]),
    )

    route={
        "token":token,
        "direction":"METEORA_TO_PUMP",
        "start_lamports":start,
        "pre_sim_net_lamports":int(opportunity["local_net"]),
        "pre_sim_min_net_lamports":int(opportunity["local_min_net"]),
        "pre_sim_bps":float(opportunity["local_bps"]),
        "pump_ixs":sell_ixs,
        "pump_index":pump_index,
        "pump_ix":pump_ix,
        "meteora_ix":meteora_ix,
        "base_alts":[],
        "original_candidates":_reverse_instruction_sets(
            sell_ixs,
            pump_index,
            meteora_ix,
        ),
    }

    return _reverse_prepend_ata_readiness(
        user,
        token,
        route,
    )




def attack_reverse(
    lane,
    token,
    snap,
    opportunity,
    slot,
    received_ns,
    generation,
):
    if lane.newer_waiting(token,generation):
        return

    if token not in SELL_TEMPLATES:
        print(
            "[REVERSE_005_HOLD] token=%s reason=NO_SELL_TEMPLATE"
            %token[:10],
            flush=True,
        )
        return

    try:
        result=_execute_route_once(USER,snap,opportunity)
    except Exception as exc:
        print(
            "[REVERSE_005_REJECT] token=%s phase=build error=%s:%s"
            %(token[:10],type(exc).__name__,str(exc)[:220]),
            flush=True,
        )
        return

    if not result.get("ok"):
        print(
            "[REVERSE_005_REJECT] token=%s phase=compile reason=%s"
            %(
                token[:10],
                result.get("compiled",{}).get("reason","UNKNOWN"),
            ),
            flush=True,
        )
        return

    compiled=result["compiled"]
    fee=int(compiled.get("fee_lamports") or 0)
    min_net=int(opportunity["local_min_net"])
    after_fee_min=min_net-fee

    print(
        "[REVERSE_005_FEE] token=%s fee=%d quote_net=%+d "
        "min_net=%+d after_fee_min=%+d"
        %(
            token[:10],
            fee,
            int(opportunity["local_net"]),
            min_net,
            after_fee_min,
        ),
        flush=True,
    )

    _live_010_certify_or_send(
        lane,
        token,
        "METEORA_TO_PUMP",
        slot,
        received_ns,
        generation,
        compiled,
        after_fee_min,
    )

    if after_fee_min<=0:
        print(
            "[REVERSE_005_HOLD] token=%s reason=AFTER_FEE_MIN_NONPOSITIVE"
            %token[:10],
            flush=True,
        )
        return

    sim=result["sim"]

    if sim.get("err") is not None:
        print(
            "[REVERSE_005_SIM_REJECT] token=%s err=%s"
            %(token[:10],str(sim.get("err"))),
            flush=True,
        )
        _canonical_sim_logs(sim)
        return

    total_ms=(time.perf_counter_ns()-received_ns)/1e6

    print(
        "[REVERSE_005_CERTIFIED] token=%s slot=%s size=0.005 "
        "quote_bps=%+.2f after_fee_min=%+d candidate=%s "
        "bytes=%d units=%s event_to_sim_ms=%.3f broadcast=FALSE"
        %(
            token[:10],
            slot,
            float(opportunity["local_bps"]),
            after_fee_min,
            compiled["candidate"],
            compiled["bytes"],
            str(sim.get("units")),
            total_ms,
        ),
        flush=True,
    )



def _assert_010_template_funding(
    template,
):
    quote=int(
        template.get(
            "template_quote_lamports",
            0,
        )
        or 0
    )

    if quote!=CANARY_TRADE_LAMPORTS:
        raise RuntimeError(
            "PUMP_TEMPLATE_FUNDING_DRIFT:"
            +str(quote)
            +":expected="
            +str(CANARY_TRADE_LAMPORTS)
        )

def same_snapshot_route(
    user,
    snap,
    opportunity
):

    direction=opportunity.get(
        "direction"
    )

    if direction=="METEORA_TO_PUMP":
        return same_snapshot_reverse_route(
            user,
            snap,
            opportunity,
        )

    if direction!="PUMP_TO_METEORA":
        raise RuntimeError(
            "DIRECTION_NOT_CERTIFIED:"
            +str(direction)
        )

    token=str(
        snap["token"]
    )

    template=(
        TEMPLATES.get(
            token
        )
    )

    if template is None:

        raise RuntimeError(
            "NO_PREBUILT_TEMPLATE:"
            +token
        )

    _assert_010_template_funding(
        template,
    )

    if template[
        "pump_pool"
    ]!=snap[
        "pump_pool"
    ]:

        raise RuntimeError(
            "PUMP_TEMPLATE_BINDING_DRIFT"
        )

    start=int(
        opportunity["start"]
    )

    base_out=int(
        opportunity[
            "pump_base_out_gross"
        ]
    )

    net_out=int(
        opportunity[
            "pump_base_out_net"
        ]
    )

    max_quote=int(
        opportunity[
            "pump_max_quote"
        ]
    )

    if (
        base_out<=0
        or net_out<=0
        or max_quote<=0
    ):

        raise RuntimeError(
            "BAD_SNAPSHOT_EXECUTION_BOUND"
        )

    execution_base_floor=max(
        1,
        base_out
        *(
            10000
            -FAST_010_PUMP_EXECUTION_TOLERANCE_BPS
        )
        //10000,
    )

    execution_net_floor=int(
        q18.token_net(
            token,
            execution_base_floor,
        )
    )

    if execution_net_floor<=0:
        raise RuntimeError(
            "PUMP_EXECUTION_NET_FLOOR_ZERO"
        )

    execution_mq=(
        q18.core.dlmm_quote_snapshot(
            snap,
            execution_net_floor,
            token,
        )
    )

    ixs=[
        copy.deepcopy(x)
        for x in template[
            "instructions"
        ]
    ]

    pump_index=int(
        template[
            "pump_index"
        ]
    )

    ixs[
        pump_index
    ]=rewrite_pump_buy_bounds(
        ixs[
            pump_index
        ],
        start,
        execution_base_floor,
    )

    pump_ix=ixs[
        pump_index
    ]

    if not any(
        a.get("pubkey")
        ==snap["pump_pool"]
        for a in (
            pump_ix.get(
                "accounts"
            )
            or []
        )
    ):

        raise RuntimeError(
            "PUMP_POOL_ACCOUNT_DRIFT"
        )

    meteora_ix=(
        build_meteora_ix_hot(
            token,
            execution_net_floor,
            dict(
                execution_mq
            ),
        )
    )

    return {
        "token":
            token,

        "start_lamports":
            start,

        "pre_sim_net_lamports":
            int(
                opportunity[
                    "local_net"
                ]
            ),

        "pre_sim_bps":
            float(
                opportunity[
                    "local_bps"
                ]
            ),

        "pump_snapshot_base_out":
            base_out,

        "pump_snapshot_net_out":
            net_out,

        "pump_snapshot_max_quote":
            max_quote,

        "pump_ixs":
            ixs,

        "pump_index":
            pump_index,

        "pump_ix":
            pump_ix,

        "meteora_ix":
            meteora_ix,

        "base_alts":[],

        "original_candidates":
            q87.las.q59
            .candidate_instruction_sets(
                ixs,
                meteora_ix,
            ),
    }







def _canonical_cached_alt_accounts(addrs):
    tables=globals().get(
        "PRELOADED_ALT_TABLES",
        {}
    )

    out={}

    for addr in list(addrs or []):
        if addr not in tables:
            raise RuntimeError(
                "CANARY_005_ALT_NOT_PRELOADED:"
                +str(addr)
            )

        out[addr]=tables[addr]

    return out


def preload_canary_saved_alts(root):
    from qseries_v2.solana_live_execution import (
        qarb_097_official_meteora_sdk_executor as q97
    )

    state=q97._load_alt_state(
        Path(root)
    )

    tables=(
        state.get("tables")
        if isinstance(state,dict)
        else {}
    )

    if not isinstance(tables,dict):
        tables={}

    token_alts={}
    addresses=[]

    for token,row in sorted(
        tables.items(),
        key=lambda x:str(x[0]),
    ):
        if not isinstance(row,dict):
            continue

        address=row.get("address")

        if not address:
            continue

        token=str(token)
        address=str(address)

        token_alts[token]=[
            address
        ]

        if address not in addresses:
            addresses.append(address)

    original=globals().get(
        "_ORIGINAL_ALT_ACCOUNTS"
    )

    if original is None:
        original=q87.c.alt_accounts
        globals()[
            "_ORIGINAL_ALT_ACCOUNTS"
        ]=original

    decoded=(
        original(addresses)
        if addresses
        else {}
    )

    if not isinstance(decoded,dict):
        raise RuntimeError(
            "CANARY_005_ALT_PRELOAD_NOT_MAPPING"
        )

    live_tables={
        str(k):v
        for k,v in decoded.items()
        if v
    }

    clean={}

    for token,alts in token_alts.items():
        usable=[
            x for x in alts
            if x in live_tables
        ]

        if usable:
            clean[token]=usable

            print(
                "[CANARY_005_ALT_READY] "
                "token=%s alt=%s"
                %(
                    token[:10],
                    usable[0],
                ),
                flush=True,
            )

        else:
            print(
                "[CANARY_005_ALT_HOLD] "
                "token=%s "
                "reason=SAVED_ALT_NOT_LIVE"
                %token[:10],
                flush=True,
            )

    globals()[
        "PRELOADED_ALTS"
    ]=clean

    globals()[
        "PRELOADED_ALT_TABLES"
    ]=live_tables

    globals()[
        "PRELOADED_SHARED_ALTS"
    ]=sorted(
        live_tables
    )

    q87.c.alt_accounts=(
        _canonical_cached_alt_accounts
    )

    print(
        "[CANARY_005_ALT_PRELOAD] "
        "ready_tokens=%d "
        "saved_token_alts=%d "
        "live_tables=%d "
        "shared_tables=%d "
        "hot_path_alt_rpc=FALSE"
        %(
            len(READY_TOKENS),
            len(clean),
            len(live_tables),
            len(
                globals().get(
                    "PRELOADED_SHARED_ALTS",
                    []
                )
            ),
        ),
        flush=True,
    )

    return clean



def _ata_create_idempotent_ix(
    payer,
    owner,
    mint,
    token_program,
):
    ata=q87.c.ata(
        owner,
        mint,
        token_program,
    )

    return {
        "programId":
            q87.c.ATA,

        "accounts":[
            {
                "pubkey":payer,
                "isSigner":True,
                "isWritable":True,
            },
            {
                "pubkey":ata,
                "isSigner":False,
                "isWritable":True,
            },
            {
                "pubkey":owner,
                "isSigner":False,
                "isWritable":False,
            },
            {
                "pubkey":mint,
                "isSigner":False,
                "isWritable":False,
            },
            {
                "pubkey":q87.c.SYSTEM,
                "isSigner":False,
                "isWritable":False,
            },
            {
                "pubkey":token_program,
                "isSigner":False,
                "isWritable":False,
            },
        ],

        # Associated Token Program:
        # 1 = CreateIdempotent
        "data":
            base64.b64encode(
                bytes([1])
            ).decode(),
    }



def _reverse_prepend_ata_readiness(user,token,route=None):
    if route is None:
        route=token
        token=str(route.get("token") or "")
    token_program=None

    template=METEORA_TEMPLATES.get(
        str(token)
    )

    if template is None:
        raise RuntimeError(
            "REVERSE_METEORA_TEMPLATE_MISSING:"
            +str(token)
        )

    token_x=str(
        template["token_x"]
    )

    token_y=str(
        template["token_y"]
    )

    fixed=list(
        template[
            "fixed_accounts"
        ]
    )

    # fixed_accounts positions:
    # 11 = token_x program
    # 12 = token_y program
    if len(fixed)<13:
        raise RuntimeError(
            "REVERSE_METEORA_FIXED_ACCOUNTS_SHORT"
        )

    if token_x==str(token):
        token_program=str(
            fixed[11][0]
        )
    elif token_y==str(token):
        token_program=str(
            fixed[12][0]
        )
    else:
        raise RuntimeError(
            "REVERSE_TOKEN_NOT_IN_METEORA_TEMPLATE"
        )

    create_wsol_ata=_ata_create_idempotent_ix(
        user,user,q87.c.WSOL,q87.c.TOKEN,
    )

    _tpl=TEMPLATES.get(str(token)) or {}
    _pi=int(_tpl.get("pump_index",0))
    _pix=list(_tpl.get("instructions") or [])[_pi]
    _pa=list(_pix.get("accounts") or [])
    if len(_pa)<12:
        raise RuntimeError("MRY015_PUMP_ACCOUNT_LAYOUT_SHORT")
    token_program=str(_pa[11]["pubkey"])

    create_token_ata=_ata_create_idempotent_ix(
        user,user,str(token),token_program,
    )

    out=dict(route)

    candidates=[]

    for name,ixs in list(
        route.get(
            "original_candidates"
        )
        or []
    ):
        ixs=list(ixs)

        candidates.append(
            (
                "ATA_READY_"+str(name),
                [create_token_ata,create_wsol_ata]+ixs,
            )
        )

    if not candidates:
        raise RuntimeError(
            "REVERSE_NO_CANDIDATES_FOR_ATA_READY"
        )

    out[
        "original_candidates"
    ]=candidates

    out[
        "reverse_ata_ready"
    ]=True

    return out


# ORACLE161_COMPILE_CONTRACT_BEGIN
def compile_current(user,route):
    # Fail closed before the native ALT compiler or any simulation call.
    from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle149_atomic_alt_compiler as _o149
    if not isinstance(route,dict):
        raise RuntimeError('ORACLE161_ROUTE_NOT_DICT')
    start=route.get('start_lamports')
    if type(start) is not int or start != CANARY_TRADE_LAMPORTS or start != 50_000_000:
        raise RuntimeError('ORACLE161_NATIVE_AMOUNT_MISMATCH')
    candidates=route.get('original_candidates')
    if not isinstance(candidates,(tuple,list)) or not candidates:
        raise RuntimeError('ORACLE161_NO_NATIVE_CANDIDATES')
    # A valid source route must contain genuine candidate instruction lists;
    # never synthesize a profitable quote or omit a required swap leg.
    for candidate in candidates:
        if not isinstance(candidate,(tuple,list)) or len(candidate)<2 or not isinstance(candidate[1],(tuple,list)) or len(candidate[1])<2:
            raise RuntimeError('ORACLE161_INVALID_NATIVE_CANDIDATE')
    print('[ORACLE161_COMPILE_ENTER] amount_lamports=50000000 candidates=%d' % len(candidates),flush=True)
    try:
        built=_o149.compile_route(user,route,BLOCKHASH.get())
    except Exception as exc:
        print('[ORACLE161_COMPILE_EXCEPTION] type=%s' % type(exc).__name__,flush=True)
        raise
    if not isinstance(built,dict):
        raise RuntimeError('ORACLE161_BAD_COMPILER_RESULT')
    if not built.get('ok'):
        print('[ORACLE161_COMPILE_HOLD] reason=%s' % str(built.get('reason','UNKNOWN'))[:140],flush=True)
        return built
    raw=built.get('raw')
    if not isinstance(raw,(bytes,bytearray)):
        raise RuntimeError('ORACLE161_NO_SERIALIZED_PACKET')
    size=len(raw)
    if size>1232 or size<100:
        raise RuntimeError('ORACLE161_SERIALIZED_PACKET_INVALID_SIZE')
    print('[ORACLE161_NATIVE_PACKET] bytes=%d amount_lamports=50000000 broadcast=FALSE' % size,flush=True)
    return _oracle162_verify_and_sign(built,user)
# ORACLE161_COMPILE_CONTRACT_END

def simulate_current(
    compiled,
    user
):
    result=q87.c.rpc(
        "simulateTransaction",
        [
            base64.b64encode(
                compiled[
                    "raw"
                ]
            ).decode(),
            {
                "encoding":"base64",
                "sigVerify":True,
                "commitment":"processed",
                "accounts":{
                    "encoding":"base64",
                    "addresses":[user],
                },
            },
        ],
    )

    if not isinstance(result,dict):
        raise RuntimeError(
            "SIM_RESULT_NOT_MAPPING:"
            +type(result).__name__
        )

    value=result.get("value")

    if not isinstance(value,dict):
        raise RuntimeError(
            "SIM_VALUE_NOT_MAPPING:"
            +type(value).__name__
        )

    return {
        "err":value.get("err"),
        "units":value.get("unitsConsumed"),
        "logs":list(value.get("logs") or []),
        "accounts":list(value.get("accounts") or []),
        "context":result.get("context"),
    }




def pump_6040_actual_base_out(sim):
    if not isinstance(sim,dict):
        return None

    err=sim.get("err")

    if not (
        isinstance(err,dict)
        and err.get(
            "InstructionError"
        )
    ):
        return None

    rows=err[
        "InstructionError"
    ]

    if (
        not isinstance(rows,list)
        or len(rows)<2
        or not isinstance(
            rows[1],
            dict
        )
        or int(
            rows[1].get(
                "Custom",
                -1
            )
        )!=6040
    ):
        return None

    logs=[
        str(x)
        for x in (
            sim.get("logs")
            or []
        )
    ]

    saw_6040=False

    for line in logs:

        if (
            "BuySlippageBelowMinBaseAmountOut"
            in line
        ):
            saw_6040=True
            continue

        if (
            saw_6040
            and "Program log: Left:"
            in line
        ):
            raw=line.split(
                "Left:",
                1
            )[1].strip()

            try:
                value=int(raw)
            except Exception:
                return None

            return (
                value
                if value>0
                else None
            )

    return None


def reprice_from_pump_chain_truth(
    snap,
    opportunity,
    actual_base_out
):
    token=str(
        snap["token"]
    )

    start=int(
        opportunity[
            "start"
        ]
    )

    actual_base_out=int(
        actual_base_out
    )

    if actual_base_out<=0:
        raise RuntimeError(
            "SAE002_BAD_CHAIN_BASE_OUT"
        )

    #
    # Apply the already-certified Token /
    # Token-2022 receipt semantics.
    #
    actual_net_token=int(
        q18.token_net(
            token,
            actual_base_out,
        )
    )

    if actual_net_token<=0:
        raise RuntimeError(
            "SAE002_CHAIN_TOKEN_NET_ZERO"
        )

    #
    # Reprice Meteora from the amount
    # PumpSwap itself says the transaction
    # can actually buy.
    #
    mq=q18.core.dlmm_quote_snapshot(
        snap,
        actual_net_token,
        token,
    )

    end=int(
        mq["raw_out"]
    )

    net=end-start

    out=dict(
        opportunity
    )

    out[
        "pump_base_out_gross"
    ]=actual_base_out

    out[
        "pump_base_out_net"
    ]=actual_net_token

    out["mq"]=mq
    out["local_end"]=end
    out["local_net"]=net

    out["local_bps"]=(
        net/start*10000.0
    )

    out[
        "pump_chain_truth"
    ]=True

    return out


def _canonical_sim_logs(sim):
    for line in (
        sim.get("logs")
        or []
    )[-15:]:

        print(
            "[CANONICAL_SIM_LOG] "
            +str(line),
            flush=True,
        )


def _execute_route_once(
    user,
    snap,
    opportunity
):
    if int(opportunity["start"])!=5_000_000:
        raise RuntimeError(
            "CANARY_005_START_NOT_EXACT:"
            +str(opportunity["start"])
        )

    if abs(float(opportunity["size_sol"])-0.005)>1e-12:
        raise RuntimeError(
            "CANARY_005_SIZE_NOT_EXACT:"
            +str(opportunity["size_sol"])
        )

    t=time.perf_counter_ns()

    route=same_snapshot_route(
        user,
        snap,
        opportunity,
    )

    build_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    t=time.perf_counter_ns()

    compiled=compile_current(
        user,
        route,
    )

    compile_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    if not compiled.get("ok"):
        return {
            "ok":False,
            "phase":"compile",
            "build_ms":build_ms,
            "compile_ms":compile_ms,
            "compiled":compiled,
        }

    fee_lamports=int(
        compiled[
            "fee_lamports"
        ]
    )

    after_fee_net=(
        int(
            opportunity[
                "local_net"
            ]
        )
        -fee_lamports
    )

    print(
        "[CANARY_005_FEE] "
        "size=0.005 "
        "gross_net=%+d "
        "fee=%d "
        "after_fee_net=%+d"
        %(
            int(opportunity["local_net"]),
            fee_lamports,
            after_fee_net,
        ),
        flush=True,
    )

    if after_fee_net<=0:
        rejected=dict(compiled)
        rejected["reason"]="AFTER_FEE_NONPOSITIVE"

        return {
            "ok":False,
            "phase":"fee",
            "reason":"AFTER_FEE_NONPOSITIVE",
            "build_ms":build_ms,
            "compile_ms":compile_ms,
            "compiled":rejected,
            "fee_lamports":fee_lamports,
            "after_fee_net":after_fee_net,
        }

    t=time.perf_counter_ns()

    sim=simulate_current(
        compiled,
        user,
    )

    sim_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    return {
        "ok":True,
        "build_ms":build_ms,
        "compile_ms":compile_ms,
        "sim_ms":sim_ms,
        "compiled":compiled,
        "sim":sim,
        "fee_lamports":fee_lamports,
        "after_fee_net":after_fee_net,
    }



def attack(
    lane,
    token,
    snap,
    opportunity,
    slot,
    received_ns,
    generation
):
    if lane.newer_waiting(
        token,
        generation
    ):
        return

    original_base_out=int(
        opportunity[
            "pump_base_out_gross"
        ]
    )

    first=_execute_route_once(
        USER,
        snap,
        opportunity,
    )

    if not first.get("ok"):

        print(
            "[CANONICAL_COMPILE_REJECT] "
            "token=%s reason=%s"
            %(
                token[:10],
                first.get(
                    "compiled",
                    {}
                ).get(
                    "reason",
                    "UNKNOWN"
                ),
            ),
            flush=True,
        )

        return

    if lane.newer_waiting(
        token,
        generation
    ):

        print(
            "[CANONICAL_SUPERSEDED] "
            "token=%s phase=first_sim"
            %token[:10],
            flush=True,
        )

        return

    sim=first["sim"]

    #
    # ========================================================
    # FIRST POSSIBILITY:
    # Transaction already works.
    # ========================================================
    #
    if sim.get("err") is None:

        total_ms=(
            time.perf_counter_ns()
            -received_ns
        )/1e6

        print(
            "[CANONICAL_SIM_PASS] "
            "token=%s "
            "slot=%s "
            "size=%.3f "
            "quote_bps=%+.2f "
            "candidate=%s "
            "bytes=%d "
            "units=%s "
            "build_ms=%.3f "
            "compile_ms=%.3f "
            "sim_ms=%.3f "
            "event_to_sim_ms=%.3f "
            "pump_truth=ORIGINAL"
            %(
                token[:10],
                slot,
                float(
                    opportunity[
                        "size_sol"
                    ]
                ),
                float(
                    opportunity[
                        "local_bps"
                    ]
                ),
                first[
                    "compiled"
                ][
                    "candidate"
                ],
                first[
                    "compiled"
                ][
                    "bytes"
                ],
                str(
                    sim.get("units")
                ),
                first[
                    "build_ms"
                ],
                first[
                    "compile_ms"
                ],
                first[
                    "sim_ms"
                ],
                total_ms,
            ),
            flush=True,
        )

        fee=int(
            first["compiled"].get("fee_lamports",0) or 0
        )
        after_fee=int(opportunity["local_net"])-fee

        _live_010_certify_or_send(
            lane,token,"PUMP_TO_METEORA",slot,
            received_ns,generation,
            first["compiled"],after_fee,
        )

        return

    #
    # ========================================================
    # SECOND POSSIBILITY:
    # PumpSwap gave exact chain output through 6040.
    # ========================================================
    #
    actual_base_out=(
        pump_6040_actual_base_out(
            sim
        )
    )

    if actual_base_out is None:

        print(
            "[CANONICAL_SIM_REJECT] "
            "token=%s "
            "slot=%s "
            "size=%.3f "
            "quote_bps=%+.2f "
            "candidate=%s "
            "bytes=%d "
            "err=%s "
            "build_ms=%.3f "
            "compile_ms=%.3f "
            "sim_ms=%.3f"
            %(
                token[:10],
                slot,
                float(
                    opportunity[
                        "size_sol"
                    ]
                ),
                float(
                    opportunity[
                        "local_bps"
                    ]
                ),
                first[
                    "compiled"
                ][
                    "candidate"
                ],
                first[
                    "compiled"
                ][
                    "bytes"
                ],
                str(
                    sim.get("err")
                ),
                first[
                    "build_ms"
                ],
                first[
                    "compile_ms"
                ],
                first[
                    "sim_ms"
                ],
            ),
            flush=True,
        )

        _canonical_sim_logs(
            sim
        )

        return

    drift=(
        actual_base_out
        -original_base_out
    )

    drift_bps=(
        drift
        /original_base_out
        *10000.0
    )

    corrected=(
        reprice_from_pump_chain_truth(
            snap,
            opportunity,
            actual_base_out,
        )
    )

    print(
        "[SAE002_PUMP_CHAIN_TRUTH] "
        "token=%s "
        "slot=%s "
        "predicted_base=%d "
        "chain_base=%d "
        "drift=%+d "
        "drift_bps=%+.2f "
        "old_quote_bps=%+.2f "
        "corrected_quote_bps=%+.2f"
        %(
            token[:10],
            slot,
            original_base_out,
            actual_base_out,
            drift,
            drift_bps,
            float(
                opportunity[
                    "local_bps"
                ]
            ),
            float(
                corrected[
                    "local_bps"
                ]
            ),
        ),
        flush=True,
    )

    fee=int(
        second["compiled"].get("fee_lamports",0) or 0
    )
    after_fee=int(corrected["local_net"])-fee

    _live_010_certify_or_send(
        lane,token,"PUMP_TO_METEORA",slot,
        received_ns,generation,
        second["compiled"],after_fee,
    )

    #
    # Chain truth killed the opportunity.
    #
    if int(
        corrected[
            "local_net"
        ]
    )<=0:

        print(
            "[SAE002_CHAIN_REPRICE_HOLD] "
            "token=%s "
            "slot=%s "
            "corrected_net=%+d "
            "corrected_bps=%+.2f"
            %(
                token[:10],
                slot,
                int(
                    corrected[
                        "local_net"
                    ]
                ),
                float(
                    corrected[
                        "local_bps"
                    ]
                ),
            ),
            flush=True,
        )

        return

    if lane.newer_waiting(
        token,
        generation
    ):

        print(
            "[CANONICAL_SUPERSEDED] "
            "token=%s "
            "phase=chain_reprice"
            %token[:10],
            flush=True,
        )

        return

    #
    # ONE retry only.
    #
    # The retry uses:
    #
    #   Pump minBaseOut = PumpSwap chain truth
    #   Meteora amountIn = transfer-adjusted chain truth
    #
    second=_execute_route_once(
        USER,
        snap,
        corrected,
    )

    if not second.get("ok"):

        print(
            "[SAE002_REPRICE_COMPILE_REJECT] "
            "token=%s reason=%s"
            %(
                token[:10],
                second.get(
                    "compiled",
                    {}
                ).get(
                    "reason",
                    "UNKNOWN"
                ),
            ),
            flush=True,
        )

        return

    sim2=second["sim"]

    total_ms=(
        time.perf_counter_ns()
        -received_ns
    )/1e6

    if sim2.get("err") is not None:

        print(
            "[SAE002_REPRICE_SIM_REJECT] "
            "token=%s "
            "slot=%s "
            "size=%.3f "
            "corrected_bps=%+.2f "
            "candidate=%s "
            "bytes=%d "
            "err=%s "
            "retry_build_ms=%.3f "
            "retry_compile_ms=%.3f "
            "retry_sim_ms=%.3f "
            "event_to_final_ms=%.3f"
            %(
                token[:10],
                slot,
                float(
                    corrected[
                        "size_sol"
                    ]
                ),
                float(
                    corrected[
                        "local_bps"
                    ]
                ),
                second[
                    "compiled"
                ][
                    "candidate"
                ],
                second[
                    "compiled"
                ][
                    "bytes"
                ],
                str(
                    sim2.get("err")
                ),
                second[
                    "build_ms"
                ],
                second[
                    "compile_ms"
                ],
                second[
                    "sim_ms"
                ],
                total_ms,
            ),
            flush=True,
        )

        _canonical_sim_logs(
            sim2
        )

        return

    print(
        "[CANONICAL_SIM_PASS] "
        "token=%s "
        "slot=%s "
        "size=%.3f "
        "quote_bps=%+.2f "
        "candidate=%s "
        "bytes=%d "
        "units=%s "
        "retry_build_ms=%.3f "
        "retry_compile_ms=%.3f "
        "retry_sim_ms=%.3f "
        "event_to_sim_ms=%.3f "
        "pump_truth=CHAIN_6040"
        %(
            token[:10],
            slot,
            float(
                corrected[
                    "size_sol"
                ]
            ),
            float(
                corrected[
                    "local_bps"
                ]
            ),
            second[
                "compiled"
            ][
                "candidate"
            ],
            second[
                "compiled"
            ][
                "bytes"
            ],
            str(
                sim2.get("units")
            ),
            second[
                "build_ms"
            ],
            second[
                "compile_ms"
            ],
            second[
                "sim_ms"
            ],
            total_ms,
        ),
        flush=True,
    )






LIVE_010_ARM_VALUE="I_ACCEPT_0_01_SOL_CANARY"
LIVE_010_STATE=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "canary_010_live_state.json"
)
LIVE_010_LOCK=threading.Lock()


def _live_010_armed():
    return (
        os.getenv(
            "QSB_ORACLE_CANARY_010_ARM",
            ""
        )
        ==LIVE_010_ARM_VALUE
    )


def _live_010_load():
    if not LIVE_010_STATE.is_file():
        return {
            "revision":"ORACLE_CANARY_005_LIVE_V1",
            "certifications":{},
            "send_attempted":False,
            "send_signature":None,
            "status":"IDLE",
        }

    row=json.loads(
        LIVE_010_STATE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(row,dict):
        raise RuntimeError(
            "LIVE_010_STATE_NOT_MAPPING"
        )

    if not isinstance(
        row.get("certifications"),
        dict
    ):
        row["certifications"]={}

    return row


def _live_010_save(row):
    LIVE_010_STATE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp=LIVE_010_STATE.with_suffix(
        ".json.tmp"
    )

    tmp.write_text(
        json.dumps(
            row,
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    tmp.replace(
        LIVE_010_STATE
    )


def _live_010_send_once(raw):
    raise RuntimeError('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED')

def _live_010_certify_or_send(
    lane,
    token,
    direction,
    slot,
    received_ns,
    generation,
    compiled,
    after_fee_lamports,
):
    if int(
        compiled.get(
            "bytes",
            MAX_TX_BYTES+1,
        )
    )>MAX_TX_BYTES:
        print(
            "[LIVE_010_HOLD] reason=SIGNED_TX_TOO_LARGE",
            flush=True,
        )
        return

    if int(
        after_fee_lamports
    )<FAST_010_MIN_REALIZED_LAMPORTS:
        print(
            "[LIVE_010_HOLD] "
            "reason=AFTER_FEE_BELOW_PROFIT_FLOOR",
            flush=True,
        )
        return

    raw=compiled.get(
        "raw"
    )

    if not isinstance(
        raw,
        (
            bytes,
            bytearray,
        ),
    ):
        print(
            "[LIVE_010_HOLD] reason=SIGNED_RAW_MISSING",
            flush=True,
        )
        return

    if not _live_010_armed():
        # ORACLE164_SIMULATION_TRUTH_BOUNDARY
        # Diagnostic only: never fall through to the armed path.
        _raw164 = compiled.get('raw')
        if compiled.get('oracle162_signature_verified') is not True:
            print('[ORACLE164_HOLD] reason=SIGNATURE_NOT_VERIFIED', flush=True)
            return
        if not isinstance(_raw164, (bytes, bytearray)) or not 100 <= len(_raw164) <= 1232:
            print('[ORACLE164_HOLD] reason=INVALID_SERIALIZED_SIZE', flush=True)
            return
        if int(compiled.get('bytes', -1)) != len(_raw164):
            print('[ORACLE164_HOLD] reason=PACKET_SIZE_MISMATCH', flush=True)
            return
        print('[ORACLE164_SIM_ENTER] direction=%s bytes=%d broadcast=FALSE' %
              (str(direction), len(_raw164)), flush=True)
        _verdict164 = 'RPC_FAILURE'
        _err164 = 'UNKNOWN'
        _units164 = None
        _logs164 = 0
        try:
            _response164 = simulate_current(compiled, USER)
            if not isinstance(_response164, dict):
                _err164 = 'NON_MAPPING_RESPONSE'
            elif 'err' not in _response164:
                _err164 = 'MISSING_ERR_FIELD'
            else:
                _units164 = _response164.get('unitsConsumed')
                _logrows164 = _response164.get('logs')
                _logs164 = len(_logrows164) if isinstance(_logrows164, list) else 0
                _rpcerr164 = _response164.get('err')
                if _rpcerr164 is None:
                    _verdict164 = 'EXECUTION_PASS_UNCERTIFIED_PROFIT'
                    _err164 = 'NONE'
                else:
                    _verdict164 = 'EXECUTION_REJECTED'
                    _err164 = str(_rpcerr164)[:160]
        except Exception as _ex164:
            _err164 = type(_ex164).__name__
        _record164 = dict(build='ORACLE164',direction=str(direction),
                          slot=int(slot),amount_lamports=50000000,
                          packet_bytes=len(_raw164),verdict=_verdict164,
                          error=_err164,units_consumed=_units164,
                          program_log_count=_logs164,broadcast=False,
                          certified_profit=False)
        try:
            _p164 = Path('runtime_state/oracle/oracle_live_execution/ORACLE164_SIMULATION_TRUTH.jsonl')
            _p164.parent.mkdir(parents=True, exist_ok=True)
            with _p164.open('a', encoding='utf-8') as _f164:
                _f164.write(json.dumps(_record164, sort_keys=True) + '\n')
        except (OSError, TypeError, ValueError):
            print('[ORACLE164_EVIDENCE_WRITE_HOLD]', flush=True)
        print('[ORACLE164_SIM_VERDICT] status=%s err=%s units=%s logs=%d broadcast=FALSE' %
              (_verdict164, _err164, str(_units164), _logs164), flush=True)
        # ORACLE165_ANCHOR_FAILURE_LINEAGE
        # Only public Solana program logs and sanitized structured failure info.
        if _verdict164 == 'EXECUTION_REJECTED':
            _index165 = None
            _code165 = None
            if isinstance(_rpcerr164, dict):
                _pair165 = _rpcerr164.get('InstructionError')
                if isinstance(_pair165, list) and len(_pair165) == 2:
                    _index165 = _pair165[0] if isinstance(_pair165[0], int) else None
                    _custom165 = _pair165[1]
                    if isinstance(_custom165, dict):
                        _code165 = _custom165.get('Custom')
            _rows165 = _logrows164 if isinstance(_logrows164, list) else []
            _keep165 = []
            for _line165 in _rows165:
                if not isinstance(_line165, str):
                    continue
                _low165 = _line165.lower()
                if ('invoke [' in _low165 or 'failed:' in _low165 or
                    'anchorerror' in _low165 or 'error code:' in _low165 or
                    'error number:' in _low165 or 'error message:' in _low165 or
                    'instruction:' in _low165 or 'program log: left:' in _low165 or
                    'program log: right:' in _low165 or 'not enough account' in _low165):
                    _keep165.append(_line165[:300])
            _evidence165 = dict(build='ORACLE165',direction=str(direction),
                token=str(token)[:12],slot=int(slot),instruction_index=_index165,
                custom_code=_code165,raw_error=str(_rpcerr164)[:180],
                log_count=len(_rows165),important_logs=_keep165[-60:],
                packet_bytes=len(_raw164),amount_lamports=50000000,
                broadcast=False,certified_profit=False)
            try:
                _fpath165 = Path('runtime_state/oracle/oracle_live_execution/ORACLE165_ANCHOR_FAILURE.jsonl')
                _fpath165.parent.mkdir(parents=True, exist_ok=True)
                with _fpath165.open('a',encoding='utf-8') as _out165:
                    _out165.write(json.dumps(_evidence165,sort_keys=True)+'\n')
            except (OSError,TypeError,ValueError):
                print('[ORACLE165_EVIDENCE_WRITE_HOLD]',flush=True)
            print('[ORACLE165_ANCHOR_FAILURE] ix=%s code=%s captured=%d/%d broadcast=FALSE' %
                  (str(_index165),str(_code165),len(_keep165),len(_rows165)),flush=True)
            for _line165 in _keep165[-16:]:
                print('[ORACLE165_PROGRAM_LOG] %s' % _line165,flush=True)
        return
    with LIVE_010_LOCK:
        state=_live_010_load()

        if bool(
            state.get(
                "send_attempted"
            )
        ):
            return

        balance=-1

        state["send_attempted"]=True
        state["status"]="SEND_ATTEMPT_MARKED"
        state["direction"]=str(direction)
        state["token"]=str(token)
        state["slot"]=int(slot)
        state["wallet_before_lamports"]=balance
        state["after_fee_gate_lamports"]=int(
            after_fee_lamports
        )
        state["attempted_unix"]=time.time()

        _live_010_save(
            state
        )

        print(
            "[LIVE_010_SEND_ATTEMPT] "
            "dir=%s token=%s slot=%s "
            "size=0.010 max_in_flight=1 "
            "no_retry=TRUE"
            %(
                direction,
                token[:10],
                slot,
            ),
            flush=True,
        )

        try:
            signature=_live_010_send_once(
                bytes(raw)
            )

        except Exception as exc:
            message=str(exc)
            low=message.lower()

            deterministic_preflight=(
                (
                    "simulation" in low
                    and "fail" in low
                )
                or (
                    "preflight" in low
                    and "fail" in low
                )
            )

            if deterministic_preflight:
                state["send_attempted"]=False
                state["status"]="PREFLIGHT_REJECTED_REARMED"
                state["send_error"]=(
                    type(exc).__name__
                    +":"
                    +message
                )

                _live_010_save(
                    state
                )

                print("[LIVE_010_PREFLIGHT_FULL] %s:%s"%(type(exc).__name__,str(exc)),flush=True)
                print(
                    "[LIVE_010_PREFLIGHT_REJECT] "
                    "token=%s error=%s:%s "
                    "broadcast=FALSE rearmed=TRUE"
                    %(
                        token[:10],
                        type(exc).__name__,
                        message[:240],
                    ),
                    flush=True,
                )
                return

            state["status"]="SEND_AMBIGUOUS_HOLD"
            state["send_error"]=(
                type(exc).__name__
                +":"
                +message
            )

            _live_010_save(
                state
            )

            print(
                "[LIVE_010_AMBIGUOUS_HOLD] "
                "token=%s error=%s:%s "
                "automatic_resend=FALSE"
                %(
                    token[:10],
                    type(exc).__name__,
                    message[:240],
                ),
                flush=True,
            )
            return

        state["send_signature"]=str(
            signature
        )
        state["status"]="SENT_WAITING_CONFIRMATION"

        _live_010_save(
            state
        )

        print(
            "[LIVE_010_SENT] signature=%s"
            %signature,
            flush=True,
        )

        tx=q96.wait_confirmed(
            signature,
            time.monotonic()+30.0,
            timeout_seconds=30,
        )

        if tx is None:
            state["status"]="CONFIRMATION_UNKNOWN_HOLD"

            _live_010_save(
                state
            )

            print(
                "[LIVE_010_CONFIRMATION_UNKNOWN] "
                "signature=%s automatic_resend=FALSE"
                %signature,
                flush=True,
            )
            return

        meta=(
            tx.get(
                "meta",
                {}
            )
            or {}
        )

        if meta.get("err") is not None:
            state["status"]="CONFIRMED_ERROR"
            state["transaction_error"]=meta.get(
                "err"
            )

            _live_010_save(
                state
            )

            print(
                "[LIVE_010_CONFIRMED_ERROR] "
                "signature=%s err=%s"
                %(
                    signature,
                    str(meta.get("err")),
                ),
                flush=True,
            )
            return

        rec=q96.reconcile(
            signature,
            tx,
            str(USER),
            str(token),
        )

        rec["execution_owner"]="ORACLE"
        rec["direction"]=str(direction)
        rec["size_sol"]=CANARY_TRADE_SOL

        state["status"]="CONFIRMED_RECONCILED"
        state["reconciliation"]=rec

        _live_010_save(
            state
        )

        delta=int(
            rec.get(
                "wallet_delta_lamports",
                0,
            )
        )

        clean=bool(
            rec.get(
                "residue_clean"
            )
        )

        print(
            "[LIVE_010_RECONCILED] "
            "signature=%s wallet_delta=%+d "
            "fee=%d token_delta=%+d "
            "wsol_delta=%+d residue_clean=%s"
            %(
                signature,
                delta,
                int(rec.get("fee_lamports",0)),
                int(rec.get("target_token_delta_raw",0)),
                int(rec.get("wsol_delta_raw",0)),
                clean,
            ),
            flush=True,
        )

        if delta>0 and clean:
            state["status"]="FIRST_REALIZED_PROFIT"

            _live_010_save(
                state
            )

            print(
                "[LIVE_010_REALIZED_PROFIT] "
                "signature=%s "
                "realized_net_lamports=%+d "
                "realized_net_sol=%+.9f"
                %(
                    signature,
                    delta,
                    delta/1e9,
                ),
                flush=True,
            )

        else:
            state["status"]="CONFIRMED_NO_REALIZED_PROFIT_HOLD"

            _live_010_save(
                state
            )

            print(
                "[LIVE_010_NO_REALIZED_PROFIT_HOLD] "
                "signature=%s wallet_delta=%+d "
                "residue_clean=%s"
                %(
                    signature,
                    delta,
                    clean,
                ),
                flush=True,
            )







FAST_010_MIN_REALIZED_LAMPORTS=10_000
FAST_010_FEE_CEILING_LAMPORTS=10_000
FAST_010_PUMP_EXECUTION_TOLERANCE_BPS=20


def _fast_010_rewrite_meteora_min_out(ix,min_out):
    out=copy.deepcopy(ix)
    raw=bytearray(base64.b64decode(out.get("data") or ""))

    if len(raw)<24:
        raise RuntimeError(
            "FAST_010_METEORA_DATA_TOO_SHORT:"+str(len(raw))
        )

    old=int(struct.unpack("<Q",bytes(raw[16:24]))[0])
    locked=max(old,int(min_out))
    raw[16:24]=struct.pack("<Q",locked)
    out["data"]=base64.b64encode(bytes(raw)).decode()
    return out,old,locked


def _mry019_align_meteora_programs(route):
    out=copy.deepcopy(route)
    token=str(out.get("token") or "")
    ix=copy.deepcopy(out.get("meteora_ix") or {})
    ac=list(ix.get("accounts") or [])

    tpl=TEMPLATES.get(token) or {}
    pi=int(tpl.get("pump_index",0))
    pump_ixs=list(tpl.get("instructions") or [])
    if pi<0 or pi>=len(pump_ixs):
        raise RuntimeError("MRY033_PUMP_INDEX_INVALID")

    pa=list(pump_ixs[pi].get("accounts") or [])
    if len(ac)<15 or len(pa)<13:
        raise RuntimeError("MRY033_LAYOUT_SHORT")

    wsol=str(q87.c.WSOL)
    if str(pa[3].get("pubkey") or "")!=token:
        raise RuntimeError("MRY033_PUMP_TARGET_MINT_MISMATCH")
    if str(pa[4].get("pubkey") or "")!=wsol:
        raise RuntimeError("MRY033_PUMP_WSOL_MINT_MISMATCH")

    target_program=str(pa[11].get("pubkey") or "")
    wsol_program=str(pa[12].get("pubkey") or "")
    x_mint=str(ac[6].get("pubkey") or "")
    y_mint=str(ac[7].get("pubkey") or "")
    if {x_mint,y_mint}!={token,wsol}:
        raise RuntimeError("MRY033_METEORA_XY_MINT_MISMATCH")

    x_program=target_program if x_mint==token else wsol_program
    y_program=target_program if y_mint==token else wsol_program

    raw=base64.b64decode(ix.get("data") or "")
    legacy=bytes([248,198,158,145,225,117,135,200])
    swap2=bytes([65,75,63,76,235,91,91,136])
    memo="MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

    if raw[:8]==legacy:
        if len(raw)<24:
            raise RuntimeError("MRY033_LEGACY_SWAP_DATA_SHORT")
        if str(ac[14].get("pubkey") or "")!=str(q87.c.DLMM):
            raise RuntimeError("MRY033_LEGACY_PROGRAM_SLOT_MISMATCH")

        ac[11]["pubkey"]=x_program
        ac[12]["pubkey"]=y_program
        memo_meta={
            "pubkey":memo,
            "isSigner":False,
            "isWritable":False,
        }
        ac=ac[:13]+[memo_meta]+ac[13:]
        raw=swap2+raw[8:24]+struct.pack("<I",0)

    elif raw[:8]==swap2:
        if len(ac)<16:
            raise RuntimeError("MRY033_SWAP2_LAYOUT_SHORT")
        ac[11]["pubkey"]=x_program
        ac[12]["pubkey"]=y_program
        ac[13]["pubkey"]=memo

    else:
        raise RuntimeError("MRY033_UNKNOWN_METEORA_SWAP_DISCRIMINATOR")

    ix["accounts"]=ac
    ix["data"]=base64.b64encode(raw).decode()
    out["meteora_ix"]=ix

    if str(out.get("direction") or "")=="METEORA_TO_PUMP":
        out["original_candidates"]=_reverse_instruction_sets(
            out["pump_ixs"],int(out["pump_index"]),ix)
    else:
        out["original_candidates"]=q87.las.q59.candidate_instruction_sets(
            out["pump_ixs"],ix)

    return out


def _fast_010_profit_lock_route(route,direction,required_final_out):
    out=copy.deepcopy(route)
    out["direction"]=str(direction)

    if direction=="PUMP_TO_METEORA":
        meteora,old_bound,new_bound=_fast_010_rewrite_meteora_min_out(
            out["meteora_ix"],required_final_out)
        out["meteora_ix"]=meteora

    elif direction=="METEORA_TO_PUMP":
        ixs=[copy.deepcopy(x) for x in out["pump_ixs"]]
        pump_index=int(out["pump_index"])
        raw=base64.b64decode(ixs[pump_index].get("data") or "")
        if len(raw)<24:
            raise RuntimeError("FAST_010_PUMP_SELL_DATA_TOO_SHORT:"+str(len(raw)))
        base_in=int(struct.unpack("<Q",raw[8:16])[0])
        old_bound=int(struct.unpack("<Q",raw[16:24])[0])
        new_bound=max(old_bound,int(required_final_out))
        ixs[pump_index]=rewrite_pump_sell_bounds(
            ixs[pump_index],base_in,new_bound)
        out["pump_ixs"]=ixs
        out["pump_ix"]=ixs[pump_index]

    else:
        raise RuntimeError("FAST_010_BAD_DIRECTION:"+str(direction))

    out=_mry019_align_meteora_programs(out)

    # ORACLE166C_FORWARD_ATA_READINESS
    # Reuse existing idempotent token+WSOL ATA initialization before both swaps.
    if direction in ("PUMP_TO_METEORA", "METEORA_TO_PUMP"):
        out=_reverse_prepend_ata_readiness(
            USER,str(out.get("token") or ""),out)
        if out.get("reverse_ata_ready") is not True:
            raise RuntimeError("ORACLE166C_ATA_NOT_CERTIFIED")
        candidates=out.get("original_candidates")
        if not isinstance(candidates,list) or not candidates:
            raise RuntimeError("ORACLE166C_NO_ATA_CANDIDATES")
        for name,ixs in candidates:
            if not str(name).startswith("ATA_READY_") or len(ixs)<4:
                raise RuntimeError("ORACLE166C_BAD_ATA_CANDIDATE")
            if any(ix.get("programId") !=
                   "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
                   for ix in ixs[:2]):
                raise RuntimeError("ORACLE166C_ATA_PREFIX_MISSING")

    return out,old_bound,new_bound


def _fast_010_prime_live_gate(direction,token,slot,after_fee_lamports):
    with LIVE_010_LOCK:
        state=_live_010_load()

        if bool(state.get("send_attempted")):
            return False

        certs=state.setdefault("certifications",{})

        certs[str(direction)]={
            "token":str(token),
            "slot":int(slot),
            "after_fee_lamports":int(after_fee_lamports),
            "certified_unix":time.time(),
            "certification_type":
                "ATOMIC_PROFIT_LOCK_PLUS_SEND_PREFLIGHT",
        }

        state["status"]="FAST_010_PREFLIGHT_ARMED"
        _live_010_save(state)

    return True



def _fast_010_refresh_latest(lane,token,snap,opportunity,slot,received_ns,generation):
    with lane.cv:
        row=lane.latest.get(token)

    if not row or int(row[3])<=int(generation):
        return (snap,opportunity,int(slot),int(received_ns),int(generation))

    latest_snap=row[0]
    latest_slot=int(row[1])
    latest_received_ns=int(row[2])
    latest_generation=int(row[3])

    rows=q18.exact_snapshot_opportunities(latest_snap,CANARY_TRADE_SOL)
    if not rows:
        print("[FAST_010_SINGLE_REFRESH_HOLD] token=%s reason=NO_QUOTES"%token[:10],flush=True)
        return None

    latest=max(rows,key=lambda x:int(x["local_net"]))

    print("[FAST_010_SINGLE_REFRESH] token=%s slot=%s dir=%s bps=%+.2f net=%+d"%
        (token[:10],latest_slot,latest["direction"],
         float(latest["local_bps"]),int(latest["local_net"])),flush=True)

    if int(latest["local_net"])<=0:
        print("[FAST_010_SINGLE_REFRESH_HOLD] token=%s reason=LATEST_NONPOSITIVE net=%+d"%
            (token[:10],int(latest["local_net"])),flush=True)
        return None

    return (latest_snap,latest,latest_slot,latest_received_ns,latest_generation)


def fast_live_attack(lane,token,snap,opportunity,slot,received_ns,generation):
    refreshed=_fast_010_refresh_latest(
        lane,token,snap,opportunity,slot,received_ns,generation)
    if refreshed is None:
        return

    snap,opportunity,slot,received_ns,generation=refreshed
    direction=str(opportunity["direction"])

    if int(opportunity["start"])!=CANARY_TRADE_LAMPORTS:
        return

    required_final=(
        CANARY_TRADE_LAMPORTS
        +FAST_010_FEE_CEILING_LAMPORTS
        +FAST_010_MIN_REALIZED_LAMPORTS
    )

    def build_locked(opp):
        route=same_snapshot_route(USER,snap,opp)
        route["direction"]=direction
        locked_route,old_bound,new_bound=_fast_010_profit_lock_route(
            route,direction,required_final)
        compiled=compile_current(USER,locked_route)
        if not compiled.get("ok"):
            raise RuntimeError(
                "FAST_010_COMPILE:"+str(compiled.get("reason","UNKNOWN")))
        fee=int(compiled.get("fee_lamports") or FAST_010_FEE_CEILING_LAMPORTS)
        if fee>FAST_010_FEE_CEILING_LAMPORTS:
            raise RuntimeError("FAST_010_FEE_ABOVE_CEILING:"+str(fee))
        if len(compiled.get("raw") or b"")>MAX_TX_BYTES:
            raise RuntimeError("FAST_010_PACKET_TOO_LARGE")
        return compiled,old_bound,new_bound,fee

    conservative=int(opportunity["local_net"])-FAST_010_FEE_CEILING_LAMPORTS
    if conservative<FAST_010_MIN_REALIZED_LAMPORTS:
        print("[FAST_010_HOLD] token=%s dir=%s reason=BELOW_FLOOR after_fee=%+d"%
              (token[:10],direction,conservative),flush=True)
        return

    try:
        locked,old_bound,new_bound,fee=build_locked(opportunity)
    except Exception as exc:
        print("[FAST_010_BUILD_REJECT] token=%s dir=%s error=%s:%s"%
              (token[:10],direction,type(exc).__name__,str(exc)[:240]),flush=True)
        return

    if direction=="PUMP_TO_METEORA":
        try:
            sim=simulate_current(locked,USER)
        except Exception as exc:
            print("[FAST_010_SIM_RPC_REJECT] token=%s error=%s:%s"%
                  (token[:10],type(exc).__name__,str(exc)[:220]),flush=True)
            return

        if sim.get("err") is not None:
            actual=pump_6040_actual_base_out(sim)
            if actual is None:
                print("[FAST_010_SIM_REJECT] token=%s err=%s"%
                      (token[:10],str(sim.get("err"))),flush=True)
                _canonical_sim_logs(sim)
                return

            corrected=reprice_from_pump_chain_truth(snap,opportunity,actual)
            corrected_after=(
                int(corrected["local_net"])
                -FAST_010_FEE_CEILING_LAMPORTS
            )

            print("[FAST_010_6040_CHAIN_TRUTH] token=%s base_out=%d old_bps=%+.2f corrected_bps=%+.2f after_fee=%+d"%
                  (token[:10],int(actual),float(opportunity["local_bps"]),
                   float(corrected["local_bps"]),corrected_after),flush=True)

            if corrected_after<FAST_010_MIN_REALIZED_LAMPORTS:
                print("[FAST_010_6040_HOLD] token=%s reason=CORRECTED_BELOW_FLOOR"%
                      token[:10],flush=True)
                return

            if lane.newer_waiting(token,generation):
                print("[FAST_010_6040_HOLD] token=%s reason=SUPERSEDED_BEFORE_REBUILD"%
                      token[:10],flush=True)
                return

            try:
                locked,old_bound,new_bound,fee=build_locked(corrected)
                sim2=simulate_current(locked,USER)
            except Exception as exc:
                print("[FAST_010_6040_REBUILD_REJECT] token=%s error=%s:%s"%
                      (token[:10],type(exc).__name__,str(exc)[:220]),flush=True)
                return

            if sim2.get("err") is not None:
                print("[FAST_010_6040_SECOND_SIM_REJECT] token=%s err=%s"%
                      (token[:10],str(sim2.get("err"))),flush=True)
                _canonical_sim_logs(sim2)
                return

            opportunity=corrected
            conservative=int(corrected["local_net"])-fee
            print("[FAST_010_6040_REBUILD_PASS] token=%s corrected_bps=%+.2f fee=%d after_fee=%+d"%
                  (token[:10],float(corrected["local_bps"]),fee,conservative),
                  flush=True)
        else:
            conservative=int(opportunity["local_net"])-fee
            print("[FAST_010_FORWARD_SIM_PASS] token=%s bps=%+.2f fee=%d after_fee=%+d"%
                  (token[:10],float(opportunity["local_bps"]),fee,conservative),
                  flush=True)
    else:
        conservative=int(opportunity["local_net"])-fee

    if conservative<FAST_010_MIN_REALIZED_LAMPORTS:
        print("[FAST_010_HOLD] token=%s reason=FINAL_AFTER_FEE_BELOW_FLOOR after_fee=%+d"%
              (token[:10],conservative),flush=True)
        return

    age_ms=(time.perf_counter_ns()-received_ns)/1e6
    print("[FAST_010_READY] token=%s dir=%s slot=%s conservative_after_fee=%+d profit_floor=%d fee=%d old_final_bound=%d locked_final_bound=%d bytes=%d event_age_ms=%.3f chain_truth=%s"%
          (token[:10],direction,slot,conservative,FAST_010_MIN_REALIZED_LAMPORTS,
           fee,old_bound,new_bound,int(locked["bytes"]),age_ms,
           bool(opportunity.get("pump_chain_truth"))),flush=True)

    _live_010_certify_or_send(
        lane,token,direction,slot,received_ns,generation,locked,conservative)






def canonical_price(
    self,
    token,
    row
):
    (
        snap,
        slot,
        received_ns,
        generation,
    )=row

    if self.newer_waiting(
        token,
        generation,
    ):
        self.scan_replaced+=1
        return

    event_age_ms=max(
        0.0,
        (
            time.perf_counter_ns()
            -received_ns
        )/1e6
    )

    self.event_start_ms.append(
        event_age_ms
    )

    t=time.perf_counter_ns()

    try:
        best=exact_best(
            self,
            token,
            snap,
            generation,
        )

    except RuntimeError as exc:
        msg=str(exc)

        if msg.startswith(
            "SUPERSEDED_"
        ):
            self.scan_replaced+=1
            return

        if "DLMM_PARTIAL" in msg:
            READY_TOKENS.discard(str(token))
            print(
                "[MRY018_DLMM_QUARANTINE] "
                "token=%s reason=DLMM_PARTIAL"
                %str(token)[:10],
                flush=True,
            )
            return

        raise

    pricing_ms=(
        time.perf_counter_ns()
        -t
    )/1e6

    self.scan_ms.append(
        pricing_ms
    )

    self.processed+=1

    if (
        self.best is None
        or int(
            best["local_net"]
        )
        >
        int(
            self.best["local_net"]
        )
    ):
        self.best=dict(
            best
        )

    net=int(
        best["local_net"]
    )

    if net<=0:
        return

    self.positive+=1

    print(
        "[CANONICAL_POSITIVE] "
        "token=%s slot=%s dir=%s "
        "size=%.3f bps=%+.2f net=%+d "
        "event_age_ms=%.3f pricing_ms=%.3f"
        %(
            token[:10],
            slot,
            best["direction"],
            float(
                best["size_sol"]
            ),
            float(
                best["local_bps"]
            ),
            net,
            event_age_ms,
            pricing_ms,
        ),
        flush=True,
    )

    fast_live_attack(
        self,
        token,
        snap,
        best,
        slot,
        received_ns,
        generation,
    )







def process_event(
    state,
    ev,
    counters,
    lane
):
    address=ev["address"]
    preg=state.get("preg",{})

    if address not in preg:
        return

    index,kind=preg[address]
    pair=state["pairs"][index]
    token=str(pair.token)

    if token not in READY_TOKENS:
        return

    try:
        changed=(
            persistent.m.pd.apply_account_event(
                pair,
                kind,
                address,
                ev["raw"],
                ev["slot"],
                ev["received_ns"],
            )
        )
    except Exception:
        counters["event_errors"]+=1
        return

    if not changed:
        return

    counters["priced_events"]+=1

    _coherence_stage(
        token,
        immutable_snapshot(pair),
        ev["slot"],
        ev["received_ns"],
        kind,
    )



async def serve_canonical(
    state,
    seconds,
    lane
):

    addresses=list(
        state.get(
            "addresses"
        )
        or []
    )

    shards=(
        persistent.m
        ._shards(
            addresses
        )
    )

    counters={
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

    queue=asyncio.Queue(
        maxsize=persistent.QUEUE_MAX
    )

    stop=asyncio.Event()

    workers=[
        asyncio.create_task(
            persistent._worker(
                i,
                shard,
                queue,
                counters,
                stop,
            )
        )
        for i,shard
        in enumerate(shards)
    ]

    print(
        "[CANONICAL_WS] "
        "accounts=%d shards=%d "
        "ready_pairs=%d"
        %(
            len(addresses),
            len(shards),
            len(
                READY_TOKENS
            ),
        ),
        flush=True,
    )

    started=time.monotonic()
    last_hb=started
    last_n=0

    try:

        while not stop.is_set():

            if (
                time.monotonic()
                -started
                >=float(seconds)
            ):
                break

            try:

                ev=await asyncio.wait_for(
                    queue.get(),
                    timeout=(
                        .002
                        if COHERENCE_PENDING
                        else .05
                    ),
                )

                process_event(
                    state,
                    ev,
                    counters,
                    lane,
                )

                _coherence_flush(
                    lane,
                    force=False,
                )

            except asyncio.TimeoutError:
                _coherence_flush(
                    lane,
                    force=False,
                )

            now=time.monotonic()

            if now-last_hb>=15.0:

                span=max(
                    .001,
                    now-last_hb
                )

                eps=(
                    counters[
                        "notifications"
                    ]
                    -last_n
                )/span

                print(
                    "[CANONICAL_HEARTBEAT] "
                    "uptime_s=%d "
                    "notifications=%d "
                    "eps=%.2f "
                    "priced_events=%d "
                    "submitted=%d "
                    "replaced=%d "
                    "processed=%d "
                    "positive=%d "
                    "scan_replaced=%d "
                    "reconnects=%d "
                    "rate_limits=%d"
                    %(
                        int(
                            now-started
                        ),
                        counters[
                            "notifications"
                        ],
                        eps,
                        counters[
                            "priced_events"
                        ],
                        lane.submitted,
                        lane.replaced,
                        lane.processed,
                        lane.positive,
                        lane.scan_replaced,
                        counters[
                            "reconnects"
                        ],
                        counters[
                            "rate_limit_disconnects"
                        ],
                    ),
                    flush=True,
                )

                last_hb=now

                last_n=counters[
                    "notifications"
                ]

    finally:

        _coherence_flush(
            lane,
            force=True,
        )

        stop.set()

        for worker in workers:
            worker.cancel()

        await asyncio.gather(
            *workers,
            return_exceptions=True
        )

    return counters




# ORACLE158_VERIFIED_ALT_PRELOAD_BEGIN
# Preload the canonical public on-chain ALT at startup, not per hot quote.
_ORACLE158_ORIGINAL_PRELOAD = preload_canary_saved_alts

def _oracle158_preload_canonical_alt():
    import base64 as _b64
    import json as _json
    from pathlib import Path as _Path
    _r = _Path('runtime_state/oracle/solana_atomic_executor/canonical_alt.json')
    _p = _Path('runtime_state/oracle/oracle_live_execution/ORACLE_151_CANONICAL_ALT_LIVE_PROOF.json')
    if not (_r.is_file() and _p.is_file()):
        raise RuntimeError('ORACLE158_CANONICAL_ALT_EVIDENCE_MISSING')
    reg = _json.loads(_r.read_text(encoding='utf-8'))
    proof = _json.loads(_p.read_text(encoding='utf-8'))
    key = reg.get('address')
    if not (isinstance(key,str) and proof.get('ok') is True
            and proof.get('active') is True and proof.get('address') == key):
        raise RuntimeError('ORACLE158_CANONICAL_ALT_PROOF_MISMATCH')
    resp = q87.c.rpc('getAccountInfo',[key,{'encoding':'base64','commitment':'confirmed'}])
    account = (resp or {}).get('value')
    if not isinstance(account,dict) or account.get('owner') != 'AddressLookupTab1e1111111111111111111111111':
        raise RuntimeError('ORACLE158_CANONICAL_ALT_OWNER_INVALID')
    data = account.get('data')
    if not isinstance(data,list) or not data:
        raise RuntimeError('ORACLE158_CANONICAL_ALT_DATA_MISSING')
    raw = _b64.b64decode(data[0],validate=True)
    if (len(raw) < 56 or (len(raw)-56)%32 or
            int.from_bytes(raw[:4],'little') != 1 or
            int.from_bytes(raw[4:12],'little') != (1<<64)-1):
        raise RuntimeError('ORACLE158_CANONICAL_ALT_INVALID_OR_INACTIVE')
    entries = [raw[j:j+32] for j in range(56,len(raw),32)]
    if not entries or len(entries)>256:
        raise RuntimeError('ORACLE158_CANONICAL_ALT_ENTRY_COUNT_INVALID')
    mapping=globals().get('PRELOADED_ALT_TABLES')
    if not isinstance(mapping,dict):
        raise RuntimeError('ORACLE158_PRELOADED_ALT_CACHE_ABSENT')
    mapping[key]=entries
    print('[ORACLE158_VERIFIED_ALT_PRELOADED] entries=%d key=%s' % (len(entries),key),flush=True)

def preload_canary_saved_alts(root):
    result = _ORACLE158_ORIGINAL_PRELOAD(root)
    _oracle158_preload_canonical_alt()
    return result
# ORACLE158_VERIFIED_ALT_PRELOAD_END

# ORACLE159_EXECUTION_BOUNDARY_BEGIN
# Nonsecret stage counters and event evidence; no wallet, raw tx, or RPC parameters.
_ORACLE159_REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE159_EXECUTION_BOUNDARY.jsonl')
_ORACLE159_COUNTS = {'attack_entry':0,'refresh_accept':0,'refresh_hold':0,
    'compile_entry':0,'compile_pass':0,'compile_hold':0,
    'sim_entry':0,'sim_success':0,'sim_error':0}

def _oracle159_record(stage, **fields):
    import json as _json
    import time as _time
    if stage in _ORACLE159_COUNTS:
        _ORACLE159_COUNTS[stage]+=1
    row={'stage':stage,'monotonic_ns':_time.monotonic_ns(),
         'counts':dict(_ORACLE159_COUNTS)}
    row.update(fields)
    try:
        _ORACLE159_REPORT.parent.mkdir(parents=True,exist_ok=True)
        with _ORACLE159_REPORT.open('a',encoding='utf-8') as f:
            f.write(_json.dumps(row,sort_keys=True)+'\n')
    except OSError:
        print('[ORACLE159_REPORT_WRITE_HOLD]',flush=True)
    if stage in ('attack_entry','refresh_accept','refresh_hold','compile_pass','compile_hold','sim_success','sim_error'):
        print('[ORACLE159_BOUNDARY] stage=%s counts=%s' %
              (stage,_ORACLE159_COUNTS),flush=True)

_ORACLE159_ORIGINAL_ATTACK=fast_live_attack
_ORACLE159_ORIGINAL_REFRESH=_fast_010_refresh_latest
_ORACLE159_ORIGINAL_COMPILE=compile_current
_ORACLE159_ORIGINAL_SIM=simulate_current

def fast_live_attack(lane,token,snap,opportunity,slot,received_ns,generation):
    _oracle159_record('attack_entry',direction=str(opportunity.get('direction','UNKNOWN')),
                      size_lamports=int(opportunity.get('start',0)),slot=int(slot))
    return _ORACLE159_ORIGINAL_ATTACK(lane,token,snap,opportunity,slot,received_ns,generation)

def _fast_010_refresh_latest(*args,**kwargs):
    result=_ORACLE159_ORIGINAL_REFRESH(*args,**kwargs)
    if result is None:
        _oracle159_record('refresh_hold')
    else:
        opp=result[1]
        _oracle159_record('refresh_accept',direction=str(opp.get('direction','UNKNOWN')),
                          start_lamports=int(opp.get('start',0)),
                          net_lamports=int(opp.get('local_net',0)))
    return result

def compile_current(user,route):
    _oracle159_record('compile_entry',direction=str(route.get('direction','UNKNOWN')))
    try:
        result=_ORACLE159_ORIGINAL_COMPILE(user,route)
        if not isinstance(result,dict) or not result.get('ok'):
            _oracle159_record('compile_hold',reason=str(result.get('reason','UNKNOWN'))[:100]
                if isinstance(result,dict) else 'NON_DICTIONARY_RESULT')
        else:
            _oracle159_record('compile_pass',tx_bytes=len(result.get('raw') or b''),
                              within_1232=(len(result.get('raw') or b'')<=1232))
        # ORACLE169_NATIVE_COMPILE_EVIDENCE: never persist bytes, wallet, or secrets.
        try:
            _c169=route.get('original_candidates') if isinstance(route,dict) else None
            _out169=[]
            if isinstance(_c169,(list,tuple)):
                for _entry169 in _c169:
                    if not isinstance(_entry169,(list,tuple)) or len(_entry169)<2:
                        continue
                    _name169,_ixs169=_entry169[0],_entry169[1]
                    if not isinstance(_ixs169,(list,tuple)):
                        continue
                    _programs169=[_ix169.get('programId') for _ix169 in _ixs169 if isinstance(_ix169,dict)]
                    _ata169='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'
                    _pump169='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
                    _meteora169=route.get('meteora_ix',{}).get('programId') if isinstance(route.get('meteora_ix'),dict) else None
                    _out169.append({'candidate':str(_name169)[:64],
                        'instruction_count':len(_ixs169),
                        'ata_first_two':len(_programs169)>=2 and _programs169[:2]==[_ata169,_ata169],
                        'pump_legs':_programs169.count(_pump169),
                        'meteora_legs':_programs169.count(_meteora169) if _meteora169 else 0,
                        'swap_order':('PUMP_TO_METEORA' if _meteora169 and _pump169 in _programs169 and _meteora169 in _programs169 and _programs169.index(_pump169)<_programs169.index(_meteora169) else 'METEORA_TO_PUMP' if _meteora169 and _pump169 in _programs169 and _meteora169 in _programs169 else 'UNRESOLVED')})
            _ok169=isinstance(result,dict) and result.get('ok') is True
            _bytes169=len(result.get('raw')) if _ok169 and isinstance(result.get('raw'),(bytes,bytearray)) else None
            _record169={'build':'ORACLE169','compiler_pass':_ok169,
                'packet_bytes':_bytes169,'fits_1232':_bytes169 is not None and 100<=_bytes169<=1232,
                'direction':str(route.get('direction','UNKNOWN')) if isinstance(route,dict) else 'UNKNOWN',
                'amount_050_sol':isinstance(route,dict) and route.get('start_lamports')==50000000,
                'candidates':_out169,'signed_simulation_certified':False,
                'profit_certified':False,'broadcast':False}
            _report169=Path('runtime_state/oracle/oracle_live_execution/ORACLE169_NATIVE_COMPILE_EVIDENCE.jsonl')
            _report169.parent.mkdir(parents=True,exist_ok=True)
            with _report169.open('a',encoding='utf-8') as _f169:
                _f169.write(json.dumps(_record169,sort_keys=True)+'\n')
            print('[ORACLE169_PACKET] pass=%s bytes=%s ata=%s two_legs=%s broadcast=FALSE' % (
                _ok169,_bytes169,any(x['ata_first_two'] for x in _out169),
                any(x['pump_legs']==1 and x['meteora_legs']==1 for x in _out169)),flush=True)
        except Exception as _err169:
            # Telemetry failure never enables a transaction or modifies trade gates.
            print('[ORACLE169_EVIDENCE_HOLD] type=%s broadcast=FALSE' % type(_err169).__name__,flush=True)
        return result
    except Exception as exc:
        _oracle159_record('compile_hold',reason=type(exc).__name__)
        raise

def simulate_current(compiled,user):
    _oracle159_record('sim_entry',tx_bytes=len(compiled.get('raw') or b''))
    try:
        result=_ORACLE159_ORIGINAL_SIM(compiled,user)
        if isinstance(result,dict) and result.get('err') is None:
            _oracle159_record('sim_success')
        else:
            _oracle159_record('sim_error',reason='RPC_SIMULATION_ERROR')
        return result
    except Exception as exc:
        _oracle159_record('sim_error',reason=type(exc).__name__)
        raise
# ORACLE159_EXECUTION_BOUNDARY_END

# ORACLE173_BLOCKHASH_BACKOFF
_ORACLE173_REFRESH=BlockhashCache.refresh

def _oracle173_refresh(self):
    import time as _time
    wait_until=getattr(self,'_oracle173_cooldown',0.0)
    if _time.monotonic()<wait_until:
        raise RuntimeError('ORACLE173_RPC_COOLDOWN_ACTIVE')
    try:
        value=_ORACLE173_REFRESH(self)
        self._oracle173_failures=0
        return value
    except Exception as exc:
        e=str(exc).lower()
        if '429' in e or 'too many requests' in e:
            import random as _random
            failures=min(6,1+getattr(self,'_oracle173_failures',0))
            self._oracle173_failures=failures
            delay=min(60.0,2.0**failures)+_random.uniform(0.0,1.0)
            self._oracle173_cooldown=_time.monotonic()+delay
            print('[ORACLE173_RPC_429] backoff_s=%.2f count=%d' %
                  (delay,failures),flush=True)
        raise

def _oracle173_loop(self):
    import time as _time
    while not self.stop:
        try: self.refresh()
        except Exception as exc:
            print('[ORACLE173_BLOCKHASH_HOLD] reason=%s' %
                  type(exc).__name__,flush=True)
        deadline=max(_time.monotonic()+10.0,
                     getattr(self,'_oracle173_cooldown',0.0))
        while not self.stop and _time.monotonic()<deadline:
            _time.sleep(min(0.2,max(0,deadline-_time.monotonic())))

def _oracle173_start(self):
    import time as _time
    import threading as _threading
    for attempt in range(1,6):
        try:
            self.refresh()
            break
        except Exception:
            if attempt==5: raise
            pause=max(0.5,getattr(self,'_oracle173_cooldown',0.0)-_time.monotonic())
            _time.sleep(min(pause,65.0))
    self.thread=_threading.Thread(target=self._loop,
        name='canonical-blockhash',daemon=True)
    self.thread.start()

BlockhashCache.refresh=_oracle173_refresh
BlockhashCache._loop=_oracle173_loop
BlockhashCache.start=_oracle173_start

# ORACLE174_EXACT_QUOTE_GATE
_ORACLE174_ORIGINAL_LOCK=_fast_010_profit_lock_route

def _oracle174_decode_data(value):
    import base64 as _base64
    if isinstance(value,(bytes,bytearray)):return bytes(value)
    if isinstance(value,(list,tuple)) and all(type(v) is int and 0<=v<=255 for v in value):
        return bytes(value)
    if isinstance(value,str):
        if value.startswith('0x'):
            try:return bytes.fromhex(value[2:])
            except ValueError:return None
        try:return _base64.b64decode(value,validate=True)
        except (ValueError,TypeError):return None
    return None

def _oracle174_validate(route,direction):
    if not isinstance(route,dict) or type(route.get('start_lamports')) is not int:
        raise RuntimeError('ORACLE174_ROUTE_AMOUNT_ABSENT')
    if route['start_lamports']!=50_000_000:
        raise RuntimeError('ORACLE174_ROUTE_NOT_EXACT_050')
    if str(direction) not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
        raise RuntimeError('ORACLE174_UNKNOWN_DIRECTION')
    candidates=route.get('original_candidates')
    if not isinstance(candidates,(list,tuple)) or not candidates:
        raise RuntimeError('ORACLE174_NATIVE_CANDIDATES_ABSENT')
    disc=bytes([198,46,21,82,180,217,232,112])
    checked=0
    for _,ixs in candidates:
        if not isinstance(ixs,(list,tuple)):
            raise RuntimeError('ORACLE174_BAD_CANDIDATE')
        for ix in ixs:
            if not isinstance(ix,dict):
                raise RuntimeError('ORACLE174_BAD_INSTRUCTION')
            if ix.get('programId')!='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA':
                continue
            raw=_oracle174_decode_data(ix.get('data'))
            if not raw or len(raw)<8:
                raise RuntimeError('ORACLE174_UNKNOWN_PUMP_DATA')
            if raw[:8]!=disc:continue
            if len(raw)<24:raise RuntimeError('ORACLE174_SHORT_BUY_DATA')
            amount=int.from_bytes(raw[8:16],'little')
            if not 45_000_000<=amount<=50_000_000:
                raise RuntimeError('ORACLE174_BUY_SPEND_NOT_050_BOUND')
            checked+=1
    if direction=='PUMP_TO_METEORA' and checked<1:
        raise RuntimeError('ORACLE174_FORWARD_BUY_NOT_VERIFIED')
    return checked

def _fast_010_profit_lock_route(route,direction,required_final_out):
    result=_ORACLE174_ORIGINAL_LOCK(route,direction,required_final_out)
    if not isinstance(result,tuple) or len(result)!=3:
        raise RuntimeError('ORACLE174_LOCK_RESULT_CHANGED')
    _oracle174_validate(result[0],direction)
    return result

# ORACLE175_ATA_ACCOUNT_IDENTITY
_ORACLE175_PREVIOUS_LOCK=_fast_010_profit_lock_route

def _oracle175_pub(meta):
    return str(meta.get('pubkey','')) if isinstance(meta,dict) else ''

def _oracle175_check(route,direction):
    if not isinstance(route,dict) or not isinstance(route.get('original_candidates'),(list,tuple)):
        raise RuntimeError('ORACLE175_ROUTE_CANDIDATES_MISSING')
    token=str(route.get('token',''))
    ata='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'
    pump='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
    wsol='So11111111111111111111111111111111111111112'
    meteora=route.get('meteora_ix')
    meteora_id=str(meteora.get('programId','')) if isinstance(meteora,dict) else ''
    if not token or not meteora_id or meteora_id in (ata,pump):
        raise RuntimeError('ORACLE175_MINT_OR_METEORA_MISSING')
    for _,ixs in route['original_candidates']:
        if not isinstance(ixs,(list,tuple)) or len(ixs)<4:
            raise RuntimeError('ORACLE175_ROUTE_TOO_SHORT')
        programs=[ix.get('programId') for ix in ixs if isinstance(ix,dict)]
        if len(programs)!=len(ixs) or programs[:2]!=[ata,ata]:
            raise RuntimeError('ORACLE175_ATA_PREFIX_ABSENT')
        addresses=[]
        for idx,mint in ((0,token),(1,wsol)):
            metas=ixs[idx].get('accounts')
            if not isinstance(metas,(list,tuple)) or len(metas)<6:
                raise RuntimeError('ORACLE175_ATA_METAS_INCOMPLETE')
            if _oracle175_pub(metas[3])!=mint:
                raise RuntimeError('ORACLE175_WRONG_ATA_MINT')
            if _oracle175_pub(metas[0])!=_oracle175_pub(metas[2]):
                raise RuntimeError('ORACLE175_ATA_PAYER_OWNER_MISMATCH')
            ata_destination=_oracle175_pub(metas[1])
            if not ata_destination or not _oracle175_pub(metas[5]):
                raise RuntimeError('ORACLE175_ATA_DEST_OR_PROGRAM_MISSING')
            addresses.append(ata_destination)
        if addresses[0]==addresses[1]:
            raise RuntimeError('ORACLE175_ATA_DEST_COLLISION')
        if programs.count(pump)!=1 or programs.count(meteora_id)!=1:
            raise RuntimeError('ORACLE175_EXACT_TWO_LEGS_MISSING')
        if direction=='PUMP_TO_METEORA' and programs.index(pump)>programs.index(meteora_id):
            raise RuntimeError('ORACLE175_WRONG_FORWARD_ORDER')
        if direction=='METEORA_TO_PUMP' and programs.index(meteora_id)>programs.index(pump):
            raise RuntimeError('ORACLE175_WRONG_REVERSE_ORDER')
        pump_ix=ixs[programs.index(pump)]
        pump_keys={_oracle175_pub(m) for m in pump_ix.get('accounts',[])}
        if addresses[0] not in pump_keys:
            raise RuntimeError('ORACLE175_PUMP_USER_TOKEN_ATA_UNREFERENCED')
    return True

def _fast_010_profit_lock_route(route,direction,required_final_out):
    result=_ORACLE175_PREVIOUS_LOCK(route,direction,required_final_out)
    if not isinstance(result,tuple) or len(result)!=3:
        raise RuntimeError('ORACLE175_PROFIT_LOCK_SHAPE')
    _oracle175_check(result[0],direction)
    return result

def run(
    seconds=300.0
):
    global USER

    root=Path.cwd()

    mry1.configure(40)
    mry2.configure_hydration(40)

    state,cap=(
        q25.prepare_once(
            root
        )
    )

    q25.bind_cached_state(
        state
    )

    token_warm=(
        install_proven_hot_math(
            state
        )
    )

    _canary_signer,USER=(
        q87.c.sim_identity()
    )

    if _canary_signer is None:
        raise RuntimeError(
            "QSB_SOLANA_PRIVATE_KEY_MISSING"
        )

    globals()["SIGNER"] = _canary_signer

    template_count=(
        prebuild_templates(
            state,
            USER
        )
    )

    meteora_template_count=(
        prebuild_meteora_templates(
            state,
            USER,
            token_warm
        )
    )

    for pair in list(
        state.get("pairs")
        or []
    ):

        token=str(
            pair.token
        )

        if token not in READY_TOKENS:
            continue

        try:

            q18.worker().warm(
                str(
                    pair.pump_pool
                )
            )

            print(
                "[CANONICAL_PUMP_WARM] "
                "token=%s pump=%s"
                %(
                    token[:10],
                    str(
                        pair.pump_pool
                    )[:12],
                ),
                flush=True,
            )

        except Exception as exc:

            READY_TOKENS.discard(
                token
            )

            print(
                "[CANONICAL_PUMP_HOLD] "
                "token=%s %s:%s"
                %(
                    token[:10],
                    type(exc).__name__,
                    str(exc)[:220],
                ),
                flush=True,
            )

    if not READY_TOKENS:

        raise RuntimeError(
            "NO_FULLY_PREWARMED_PAIRS"
        )

    reverse_sell_template_count=(
        prebuild_sell_templates(
            state,
            USER,
        )
    )

    print(
        "[REVERSE_005_PRELOAD] "
        "sell_templates=%d broadcast=FALSE"
        %reverse_sell_template_count,
        flush=True,
    )

    m14.preload(preload_canary_saved_alts,root)

    BLOCKHASH.start()

    lane=q20.LatestStateLane()

    lane._price=(
        canonical_price
        .__get__(
            lane,
            q20.LatestStateLane,
        )
    )

    lane.start()

    print(
        "[LIVE_010_MODE] "
        "armed=%s exact_size=0.050 "
        "max_in_flight=1 "
        "requires_prior_certification=FALSE "
        "automatic_resend=FALSE"
        %_live_010_armed(),
        flush=True,
    )

    print(
        "[SOLANA-ATOMIC-EXECUTOR] "
        "CANONICAL FULL REPLACEMENT",
        flush=True,
    )

    print(
        "[TRANSPORT] "
        "direct persistent WebSocket workers only",
        flush=True,
    )

    print(
        "[OLD_SIMULATION_LANE] "
        "NOT CREATED",
        flush=True,
    )

    print(
        "[OLD_INITIAL_SCAN] "
        "NOT CALLED",
        flush=True,
    )

    print(
        "[QARB-023_EXECUTION_PATH] "
        "ABSENT",
        flush=True,
    )

    print(
        "[TOKEN_NET] "
        "ORACLE-023 persistent worker prewarmed=%d"
        %len(token_warm),
        flush=True,
    )

    print(
        "[PUMP_TEMPLATE] "
        "startup_only=%d "
        "hot_path_http=FALSE"
        %template_count,
        flush=True,
    )

    print(
        "[METEORA_TEMPLATE] "
        "startup_only=%d "
        "hot_path_rpc=FALSE "
        "hot_path_getProgramAccounts=FALSE"
        %meteora_template_count,
        flush=True,
    )

    print(
        "[SNAPSHOT] "
        "deep-copied immutable DLMM + Pump reserves",
        flush=True,
    )

    print(
        "[COHERENCE] "
        "quiet_ms=3 max_hold_ms=12 "
        "same-slot latest-state coalescing=TRUE",
        flush=True,
    )

    print(
        "[FRESHNESS] "
        "latest-generation wins; "
        "NO arbitrary 750ms rejection",
        flush=True,
    )

    print(
        "[PUMP_EXECUTION_BOUND] "
        "BuyExactQuoteIn rewritten from exact "
        "same-snapshot spendableQuote + minBaseOut",
        flush=True,
    )

    print(
        "[BROADCAST] armed-live-direct-send-enabled",
        flush=True,
    )

    try:

        asyncio.run(
            mry5.serve_rotating(
                __import__(__name__,fromlist=['*']),
                root,
                state,
                float(seconds),
                lane,
            )
        )

    finally:

        lane.close()

        BLOCKHASH.close()

        if getattr(
            q18,
            "_worker",
            None
        ) is not None:

            q18._worker.close()
            q18._worker=None

        try:
            q25.q23.worker().close()

        except Exception:
            pass

    print(
        "[CANONICAL_COMPLETE] "
        "submitted=%d "
        "replaced=%d "
        "processed=%d "
        "positive=%d "
        "scan_replaced=%d"
        %(
            lane.submitted,
            lane.replaced,
            lane.processed,
            lane.positive,
            lane.scan_replaced,
        ),
        flush=True,
    )

    return 0







def main(argv=None):

    p=argparse.ArgumentParser()

    p.add_argument(
        "--seconds",
        type=float,
        default=300.0,
    )

    a=p.parse_args(
        argv
    )

    return run(
        a.seconds
    )


if __name__=="__main__":

    raise SystemExit(
        main()
    )


# ORACLE087_FORWARD_WSOL_FUNDING_CUTOVER
_oracle087_previous_same_snapshot_route = same_snapshot_route
def same_snapshot_route(user, snap, opportunity):
    from .oracle_087_wsol_funding_alignment import route_funding
    route = _oracle087_previous_same_snapshot_route(user, snap, opportunity)
    return route_funding(route, user, q87)
