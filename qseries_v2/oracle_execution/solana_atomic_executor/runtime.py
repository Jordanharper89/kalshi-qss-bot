from __future__ import annotations

import argparse
import asyncio
import base64
import copy
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

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_087_two_second_compaction_liquidity_repair as q87
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

MAX_TX_BYTES=1232

FAST_SIZES=(
    0.001,
    0.010,
    0.050,
)

EXPAND_SIZES=(
    0.180,
    0.500,
    1.400,
)

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
        token=str(
            pair.token
        )

        pool=str(
            pair.pump_pool
        )

        last=None

        for attempt in range(1,4):

            try:

                ixs,_=(
                    q87.las.q59
                    .native_pump_buy_ixs(
                        user,
                        pool,
                        1_000_000,
                    )
                )

                pos=pump_ix_position(
                    ixs
                )

                TEMPLATES[
                    token
                ]={
                    "pump_pool":
                        pool,

                    "instructions":[
                        copy.deepcopy(x)
                        for x in ixs
                    ],

                    "pump_index":
                        int(pos),
                }

                READY_TOKENS.add(
                    token
                )

                print(
                    "[CANONICAL_TEMPLATE_READY] "
                    "token=%s "
                    "pump=%s "
                    "instructions=%d "
                    "attempt=%d"
                    %(
                        token[:10],
                        pool[:12],
                        len(ixs),
                        attempt,
                    ),
                    flush=True,
                )

                break

            except Exception as exc:

                last=exc

                print(
                    "[CANONICAL_TEMPLATE_RETRY] "
                    "token=%s "
                    "attempt=%d "
                    "%s:%s"
                    %(
                        token[:10],
                        attempt,
                        type(exc).__name__,
                        str(exc)[:240],
                    ),
                    flush=True,
                )

                time.sleep(
                    .4*attempt
                )

        if token not in READY_TOKENS:

            print(
                "[CANONICAL_TEMPLATE_HOLD] "
                "token=%s "
                "reason=%s:%s"
                %(
                    token[:10],
                    type(last).__name__
                    if last
                    else "UNKNOWN",
                    str(last)[:240]
                    if last
                    else "",
                ),
                flush=True,
            )

    if not READY_TOKENS:
        raise RuntimeError(
            "NO_CANONICAL_PUMP_TEMPLATES"
        )

    return len(
        READY_TOKENS
    )



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



def build_meteora_ix_hot(
    token,
    input_amount,
    quote_result
):
    #
    # HOT PATH:
    #
    # ZERO RPC
    # ZERO HTTP
    # ZERO getProgramAccounts
    #
    template=(
        METEORA_TEMPLATES.get(
            str(token)
        )
    )

    if template is None:
        raise RuntimeError(
            "METEORA_TEMPLATE_MISSING:"
            +str(token)
        )

    swap_for_y=bool(
        quote_result.get(
            "swap_for_y"
        )
    )

    if (
        swap_for_y
        !=template[
            "swap_for_y"
        ]
    ):
        raise RuntimeError(
            "DLMM_QUOTE_DIRECTION_MISMATCH"
        )

    arrays=list(
        template[
            "arrays"
        ]
    )

    crossed=max(
        1,
        int(
            quote_result.get(
                "bins_crossed"
            )
            or 1
        ),
    )

    n=min(
        len(arrays),
        max(
            1,
            (
                crossed+69
            )//70,
        ),
    )

    if swap_for_y:
        chosen=arrays[:n]
    else:
        chosen=list(
            reversed(
                arrays
            )
        )[:n]

    accounts=list(
        template[
            "fixed_accounts"
        ]
    )

    accounts.extend(
        (
            address,
            False,
            True,
        )
        for _,address
        in chosen
    )

    min_out=(
        int(
            quote_result[
                "raw_out"
            ]
        )
        *(
            10000
            -q87.las.q59.SLIPPAGE_BPS
        )
        //10000
    )

    data=(
        bytes([
            248,
            198,
            158,
            145,
            225,
            117,
            135,
            200,
        ])
        +struct.pack(
            "<QQ",
            int(
                input_amount
            ),
            int(
                min_out
            ),
        )
    )

    return {
        "programId":
            q87.c.DLMM,

        "accounts":[
            {
                "pubkey":
                    pubkey,

                "isSigner":
                    signer,

                "isWritable":
                    writable,
            }
            for (
                pubkey,
                signer,
                writable,
            )
            in accounts
        ],

        "data":
            base64.b64encode(
                data
            ).decode(),
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


def exact_best(lane,token,snap,generation):
    sizes=(
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

    rows=[]

    for size in sizes:
        rows.extend(
            q18.exact_snapshot_opportunities(
                snap,
                size,
            )
        )

    if not rows:
        raise RuntimeError(
            "SAE005E_NO_SIZE_QUOTES"
        )

    return max(
        rows,
        key=lambda x:int(
            x["local_net"]
        ),
    )



def same_snapshot_route(
    user,
    snap,
    opportunity
):

    if opportunity.get(
        "direction"
    )!="PUMP_TO_METEORA":

        raise RuntimeError(
            "DIRECTION_NOT_CERTIFIED:"
            +str(
                opportunity.get(
                    "direction"
                )
            )
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
        base_out,
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
            net_out,
            dict(
                opportunity["mq"]
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


def compile_current(
    user,
    route
):

    blockhash=(
        BLOCKHASH.get()
    )

    candidates=list(
        q87.repaired_candidates(
            route
        )
    )

    attempts=[]

    for candidate in candidates:

        name=str(
            candidate.get(
                "name",
                "UNKNOWN"
            )
        )

        if (
            "PUMP_METEORA_ONLY"
            in name
        ):
            continue

        try:

            comp=(
                q87.compile_candidate(
                    user,
                    candidate[
                        "instructions"
                    ],
                    [[]],
                    blockhash,
                )
            )

        except Exception as exc:

            attempts.append({
                "candidate":
                    name,

                "error":
                    "%s:%s"
                    %(
                        type(exc).__name__,
                        str(exc),
                    ),
            })

            continue

        if not isinstance(
            comp,
            dict
        ):

            attempts.append({
                "candidate":
                    name,

                "error":
                    "NON_MAPPING_COMPILE",
            })

            continue

        attempts.append({
            "candidate":
                name,

            "ok":
                bool(
                    comp.get(
                        "ok"
                    )
                ),

            "error":
                comp.get(
                    "error"
                ),
        })

        if not comp.get(
            "ok"
        ):
            continue

        raw=comp[
            "unsigned"
        ]

        size=len(raw)

        print(
            "[CANONICAL_COMPILE] "
            "candidate=%s "
            "bytes=%d"
            %(
                name,
                size,
            ),
            flush=True,
        )

        if size>MAX_TX_BYTES:
            continue

        return {
            "ok":True,

            "candidate":
                name,

            "bytes":
                size,

            "msg":
                comp["msg"],

            "raw":
                raw,

            "attempts":
                attempts,
        }

    return {
        "ok":False,

        "reason":
            "NO_LEGAL_COMPACT_TX",

        "attempts":
            attempts,
    }


def simulate_current(
    compiled,
    user
):
    #
    # IMPORTANT:
    #
    # Solana simulateTransaction returns:
    #
    # {
    #   "context": {...},
    #   "value": {
    #       "err": ...,
    #       "logs": ...,
    #       "unitsConsumed": ...,
    #       "accounts": ...
    #   }
    # }
    #
    # The old core helper incorrectly read
    # err/logs/units from the OUTER object.
    #
    # Canonical execution must decode the
    # nested value object directly.
    #
    result=q87.c.rpc(
        "simulateTransaction",
        [
            base64.b64encode(
                compiled[
                    "raw"
                ]
            ).decode(),
            {
                "encoding":
                    "base64",

                "sigVerify":
                    False,

                "commitment":
                    "processed",

                "accounts":{
                    "encoding":
                        "base64",

                    "addresses":[
                        user
                    ],
                },
            },
        ],
    )

    if not isinstance(
        result,
        dict
    ):
        raise RuntimeError(
            "SIM_RESULT_NOT_MAPPING:"
            +type(
                result
            ).__name__
        )

    value=result.get(
        "value"
    )

    if not isinstance(
        value,
        dict
    ):
        raise RuntimeError(
            "SIM_VALUE_NOT_MAPPING:"
            +type(
                value
            ).__name__
        )

    return {
        "err":
            value.get(
                "err"
            ),

        "units":
            value.get(
                "unitsConsumed"
            ),

        "logs":
            list(
                value.get(
                    "logs"
                )
                or []
            ),

        "accounts":
            list(
                value.get(
                    "accounts"
                )
                or []
            ),

        "context":
            result.get(
                "context"
            ),
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

    t=(
        time.perf_counter_ns()
    )

    try:

        best=exact_best(
            self,
            token,
            snap,
            generation,
        )

    except RuntimeError as exc:

        if str(exc).startswith(
            "SUPERSEDED_"
        ):
            self.scan_replaced+=1
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
            self.best[
                "local_net"
            ]
        )
    ):

        self.best=dict(
            best
        )

    print(
        "[CANONICAL_PRICE] "
        "token=%s "
        "slot=%s "
        "dir=%s "
        "size=%.3f "
        "bps=%+.2f "
        "net=%+d "
        "event_age_ms=%.3f "
        "pricing_ms=%.3f"
        %(
            token[:10],
            slot,
            best[
                "direction"
            ],
            float(
                best[
                    "size_sol"
                ]
            ),
            float(
                best[
                    "local_bps"
                ]
            ),
            int(
                best[
                    "local_net"
                ]
            ),
            event_age_ms,
            pricing_ms,
        ),
        flush=True,
    )

    if int(
        best[
            "local_net"
        ]
    )<=0:
        return

    self.positive+=1

    if best[
        "direction"
    ]!="PUMP_TO_METEORA":

        print(
            "[CANONICAL_POSITIVE_HOLD] "
            "token=%s dir=%s"
            %(
                token[:10],
                best[
                    "direction"
                ],
            ),
            flush=True,
        )

        return

    attack(
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

    address=ev[
        "address"
    ]

    preg=state.get(
        "preg",
        {}
    )

    if address not in preg:
        return

    index,kind=preg[
        address
    ]

    pair=state[
        "pairs"
    ][index]

    token=str(
        pair.token
    )

    if token not in READY_TOKENS:
        return

    try:

        changed=(
            persistent.m.pd
            .apply_account_event(
                pair,
                kind,
                address,
                ev["raw"],
                ev["slot"],
                ev["received_ns"],
            )
        )

    except Exception:

        counters[
            "event_errors"
        ]+=1

        return

    if not changed:
        return

    counters[
        "priced_events"
    ]+=1

    lane.submit(
        token,
        immutable_snapshot(
            pair
        ),
        ev[
            "slot"
        ],
        ev[
            "received_ns"
        ],
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
                    timeout=.25,
                )

                process_event(
                    state,
                    ev,
                    counters,
                    lane,
                )

            except asyncio.TimeoutError:
                pass

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

        stop.set()

        for worker in workers:
            worker.cancel()

        await asyncio.gather(
            *workers,
            return_exceptions=True
        )

    return counters


def run(
    seconds=300.0
):
    global USER

    root=Path.cwd()

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

    _,USER=(
        q87.c.sim_identity()
    )

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
        "[BROADCAST] disabled",
        flush=True,
    )

    try:

        asyncio.run(
            serve_canonical(
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
