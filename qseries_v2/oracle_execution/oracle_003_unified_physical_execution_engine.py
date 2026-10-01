from __future__ import annotations

import atexit
import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_013_pumpswap_program_discovery
    as oracle013_discovery
)

from qseries_v2.oracle_execution import (
    oracle_001_live_solana_executor
    as base
)

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_080_single_runtime_dynamic_mriya_supervisor as q80
)
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import (
    qarb_081_proven_arbitrage_lifecycle_certification as q81
)

EXECUTION_OWNER="ORACLE"
ORACLE_EXECUTION_AUTHORITY=True

MICRO_SOL=0.001
MICRO_LAMPORTS=1_000_000

MAX_TX_BYTES=1232

NODE_DIR=Path(
    "qseries_v2/"
    "oracle_strategy_intelligence/"
    "solana_money/"
    "qsb059d_pump_native"
)

STATE=Path(
    "runtime_state/oracle/"
    "unified_physical_execution/"
    "oracle_003_state.json"
)

LEDGER=Path(
    "runtime_state/oracle/"
    "unified_physical_execution/"
    "oracle_003_ledger.jsonl"
)


def save(payload):
    STATE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tmp=STATE.with_suffix(
        ".tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str
        ),
        encoding="utf-8"
    )

    tmp.replace(STATE)


def append(payload):
    LEDGER.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with LEDGER.open(
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            json.dumps(
                payload,
                sort_keys=True,
                default=str
            )
            +"\n"
        )


def rpc(
    method,
    params,
    timeout=20
):
    url=os.getenv(
        "SOLANA_RPC_URL",
        "https://api.mainnet-beta.solana.com"
    )

    body=json.dumps({
        "jsonrpc":"2.0",
        "id":1,
        "method":method,
        "params":params,
    }).encode()

    delay=0.75
    last=None

    for attempt in range(
        1,
        6
    ):
        req=urllib.request.Request(
            url,
            data=body,
            headers={
                "content-type":
                    "application/json",

                "user-agent":
                    "oracle-unified-executor/3.0",
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(
                req,
                timeout=timeout
            ) as r:
                j=json.loads(
                    r.read().decode()
                )

            if j.get("error"):
                raise RuntimeError(
                    "RPC_%s:%s"%(
                        method,
                        json.dumps(
                            j["error"],
                            sort_keys=True
                        )
                    )
                )

            return j.get(
                "result"
            )

        except urllib.error.HTTPError as exc:
            last=exc

            if (
                exc.code!=429
                or attempt==5
            ):
                raise

            print(
                "[RPC_429_BACKOFF] "
                "method=%s attempt=%d"%(
                    method,
                    attempt
                ),
                flush=True
            )

            time.sleep(delay)

            delay=min(
                delay*2.0,
                8.0
            )

        except urllib.error.URLError as exc:
            last=exc

            if attempt==5:
                raise

            time.sleep(delay)

            delay=min(
                delay*2.0,
                8.0
            )

    raise RuntimeError(
        "RPC_RETRY_EXHAUSTED:"
        +str(last)
    )


# All inherited transaction compilation/simulation RPC
# now uses the same resilient Oracle RPC boundary.
base._rpc=rpc


def node_json(
    script,
    payload,
    timeout=45
):
    p=subprocess.run(
        [
            "node",
            script
        ],
        cwd=NODE_DIR,
        input=json.dumps(
            payload
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout
    )

    if p.returncode!=0:
        raise RuntimeError(
            "NODE_FAILED:"
            +p.stderr[-3000:]
        )

    try:
        out=json.loads(
            p.stdout.strip()
            .splitlines()[-1]
        )
    except Exception:
        raise RuntimeError(
            "NODE_BAD_JSON:"
            +p.stdout[-3000:]
        )

    if not out.get("ok"):
        raise RuntimeError(
            str(
                out.get(
                    "reason"
                )
            )
        )

    return out


def pump_max_quote_envelope():
    bps=int(
        base.q87.las.q59
        .SLIPPAGE_BPS
    )

    if bps<0:
        raise RuntimeError(
            "NEGATIVE_PUMP_SLIPPAGE"
        )

    # integer ceiling
    return (
        MICRO_LAMPORTS
        *(10000+bps)
        +9999
    )//10000


def pump_min_base_out(
    pump_ix
):
    raw=base64.b64decode(
        pump_ix.get("data") or ""
    )

    BUY=bytes([
        102,6,61,18,
        1,218,235,234
    ])

    BUY_EXACT=bytes([
        198,46,21,82,
        180,217,232,112
    ])

    if len(raw)<24:
        raise RuntimeError(
            "PUMP_DATA_TOO_SHORT"
        )

    disc=raw[:8]

    a=int.from_bytes(
        raw[8:16],
        "little"
    )

    b=int.from_bytes(
        raw[16:24],
        "little"
    )

    allowed=(
        pump_max_quote_envelope()
    )

    if disc==BUY:
        # PumpSwap BUY:
        #
        # a = exact base_amount_out
        # b = max_quote_amount_in
        #
        # 0.001 SOL remains the quoted strategy capital.
        # max_quote_amount_in may only exceed that principal
        # by the already-configured slippage envelope.
        base_amount_out=a
        max_quote_amount_in=b

        if (
            max_quote_amount_in
            >allowed
        ):
            raise RuntimeError(
                "PUMP_MAX_QUOTE_OUTSIDE_SLIPPAGE_ENVELOPE:"
                +str(max_quote_amount_in)
                +":allowed="
                +str(allowed)
            )

        if base_amount_out<=0:
            raise RuntimeError(
                "PUMP_BASE_AMOUNT_ZERO"
            )

        return base_amount_out

    if disc==BUY_EXACT:
        # PumpSwap BUY_EXACT_QUOTE_IN:
        #
        # a = spendable_quote_in
        # b = min_base_amount_out
        #
        # This form is exact-input and therefore may not exceed
        # the 0.001 SOL strategy principal itself.
        spendable_quote_in=a
        min_base_amount_out=b

        if (
            spendable_quote_in
            >MICRO_LAMPORTS
        ):
            raise RuntimeError(
                "PUMP_EXACT_INPUT_EXCEEDS_PRINCIPAL:"
                +str(
                    spendable_quote_in
                )
            )

        if min_base_amount_out<=0:
            raise RuntimeError(
                "PUMP_MINIMUM_ZERO"
            )

        return min_base_amount_out

    raise RuntimeError(
        "PUMP_UNKNOWN_BUY_DISCRIMINATOR:"
        +disc.hex()
    )

def net_received(
    mint,
    gross
):
    j=node_json(
        "oracle003_token_net.mjs",
        {
            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "mint":
                str(mint),

            "gross":
                int(gross),
        },
        timeout=30
    )

    return {
        "gross":
            int(j["gross"]),

        "fee":
            int(j["fee"]),

        "net":
            int(j["net"]),

        "program":
            j.get("program"),
    }


def meteora_swap(
    user,
    pair,
    amount
):
    j=node_json(
        "oracle003_meteora_swap.mjs",
        {
            "rpc":
                os.getenv(
                    "SOLANA_RPC_URL",
                    "https://api.mainnet-beta.solana.com"
                ),

            "user":
                str(user),

            "pool":
                str(
                    pair.meteora_pool
                ),

            "inputMint":
                str(pair.token),

            "outputMint":
                str(
                    base.q87.c.WSOL
                ),

            "amount":
                int(amount),

            "slippageBps":
                int(
                    base.q87.las.q59
                    .SLIPPAGE_BPS
                ),
        }
    )

    return {
        "consumed":
            int(
                j["consumedIn"]
            ),

        "out":
            int(j["out"]),

        "min_out":
            int(j["minOut"]),

        "depth":
            int(
                j.get(
                    "loadedBinArrays",
                    0
                )
            ),

        "quote_source":
            j.get(
                "quoteSource"
            ),

        "bin_arrays":
            list(
                j.get(
                    "binArrays"
                )
                or []
            ),

        "instructions":
            list(
                j.get(
                    "instructions"
                )
                or []
            ),
    }


def exact_route(
    user,
    pair
):
    # --------------------------------------------------------
    # EXACT SAME PHYSICAL ROUTE FOR PAPER AND LIVE
    # --------------------------------------------------------

    pump_ixs,pump_quote_out=(
        base.q87.las.q59
        .native_pump_buy_ixs(
            user,
            pair.pump_pool,
            MICRO_LAMPORTS
        )
    )

    positions=[
        i
        for i,x in enumerate(
            pump_ixs
        )
        if x.get(
            "programId"
        )==base.q87.c.PUMP
    ]

    if len(positions)!=1:
        raise RuntimeError(
            "PUMP_IX_COUNT:"
            +str(len(positions))
        )

    pi=positions[0]
    pump_ix=pump_ixs[pi]

    # IMPORTANT:
    # Do not use the optimistic Pump quote as Meteora input.
    # Extract the minimum amount the Pump instruction itself
    # guarantees on-chain.
    pump_minimum=pump_min_base_out(
        pump_ix
    )

    received=net_received(
        pair.token,
        pump_minimum
    )

    spendable=int(
        received["net"]
    )

    if spendable<=0:
        raise RuntimeError(
            "PUMP_NET_MINIMUM_ZERO"
        )

    meteora=meteora_swap(
        user,
        pair,
        spendable
    )

    if (
        meteora["consumed"]
        !=spendable
    ):
        raise RuntimeError(
            "METEORA_PARTIAL_INPUT"
        )

    guaranteed_end=int(
        meteora[
            "min_out"
        ]
    )

    guaranteed_net=(
        guaranteed_end
        -MICRO_LAMPORTS
    )

    guaranteed_bps=(
        guaranteed_net
        /MICRO_LAMPORTS
        *10000.0
    )

    if guaranteed_net<=0:
        raise RuntimeError(
            "GUARANTEED_NET_NONPOSITIVE:"
            +str(
                guaranteed_net
            )
        )

    if (
        guaranteed_bps
        <
        base.q87.las.q59
        .MIN_NET_BPS
    ):
        raise RuntimeError(
            "GUARANTEED_BPS_BELOW_GATE:"
            +str(
                guaranteed_bps
            )
        )

    pre=list(
        pump_ixs[:pi]
    )

    post=list(
        pump_ixs[
            pi+1:
        ]
    )

    full=(
        pre
        +[pump_ix]
        +meteora[
            "instructions"
        ]
        +post
    )

    return {
        "token":
            pair.token,

        "start_lamports":
            MICRO_LAMPORTS,

        "pump_quote_out":
            int(
                pump_quote_out
            ),

        "pump_minimum_out":
            pump_minimum,

        "pump_transfer_fee":
            received["fee"],

        "pump_spendable_out":
            spendable,

        "meteora_min_out":
            guaranteed_end,

        "meteora_quote_out":
            meteora["out"],

        "meteora_bin_depth":
            meteora["depth"],

        "meteora_quote_source":
            meteora.get(
                "quote_source"
            ),

        "pre_sim_net_lamports":
            guaranteed_net,

        "pre_sim_bps":
            guaranteed_bps,

        "base_alts":
            [],

        "original_candidates":[
            (
                "ORACLE_UNIFIED_FULL",
                full
            )
        ],
    }


def prepare_exact_packet(
    root,
    row,
    kp,
    user
):
    pair_map=base.hydrate_rows(
        root,
        [row]
    )

    pair=pair_map.get(
        row["token"]
    )

    if pair is None:
        return {
            "ok":False,
            "reason":
                "PAIR_MISSING"
        }

    try:
        route=exact_route(
            user,
            pair
        )

    except Exception as exc:
        return {
            "ok":False,

            "reason":
                type(exc).__name__
                +":"
                +str(exc)
        }

    compiled=base.compile_signed(
        user,
        kp,
        route,
        "ORACLE_UNIFIED_FULL"
    )

    if not compiled.get("ok"):
        return {
            "ok":False,

            "reason":
                compiled.get(
                    "reason",
                    "COMPILE_REJECT"
                ),

            "attempts":
                compiled.get(
                    "attempts",
                    []
                )
        }

    raw=compiled["raw"]

    if len(raw)>MAX_TX_BYTES:
        return {
            "ok":False,
            "reason":
                "SIGNED_PACKET_TOO_LARGE"
        }

    sim=base.signed_simulation(
        raw
    )

    if sim.get("err") is not None:
        return {
            "ok":False,

            "reason":
                "SIGNED_SIM_ERROR",

            "simulation":
                sim
        }

    return {
        "ok":True,

        "raw":
            raw,

        "bytes":
            len(raw),

        "candidate":
            compiled[
                "candidate"
            ],

        "simulation":
            sim,

        "route":
            route,

        "token":
            row["token"],

        "fresh_net_lamports":
            route[
                "pre_sim_net_lamports"
            ],

        "fresh_bps":
            route[
                "pre_sim_bps"
            ],
    }



_DISCOVERY_CHILD=None
_BROAD_DISCOVERY_CHILD=None



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


def _stop_oracle_discovery():
    global _DISCOVERY_CHILD

    _stop_broad_discovery()

    child=_DISCOVERY_CHILD

    _DISCOVERY_CHILD=None

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


def _ensure_oracle_discovery(
    root,
    seconds=150.0
):
    import subprocess
    import sys

    global _DISCOVERY_CHILD

    if (
        _DISCOVERY_CHILD is not None
        and _DISCOVERY_CHILD.poll() is None
    ):
        return _DISCOVERY_CHILD

    _DISCOVERY_CHILD=subprocess.Popen(
        [
            sys.executable,
            "run_qarb_043b_paced_mriya_token_discovery.py",
            "--seconds",
            str(
                max(
                    30.0,
                    float(seconds)
                )
            )
        ],
        cwd=str(
            Path(root)
        ),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return _DISCOVERY_CHILD


def _recent_mriya_count(
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


def refresh_live_universe_rows(
    root
):
    root=Path(root)

    hot_seconds=min(
        90.0,
        float(
            q80.q45.HOT
        )
    )

    recent=_recent_mriya_count(
        hot_seconds
    )

    if not recent:
        return []

    payload,active=(
        _classify_merged_discovery()
    )

    now=time.time()

    rows=[]

    for row in active:

        life=(
            row.get(
                "lifecycle"
            )
            or {}
        )

        age=float(
            life.get(
                "seconds_since_last_seen",
                1e18
            )
        )

        # LIVE-MONEY INTAKE:
        # HOT only.
        if age>hot_seconds:
            continue

        token=row.get(
            "token"
        )

        pump=row.get(
            "pump_pool"
        )

        meta=(
            row.get(
                "meteora_meta"
            )
            or {}
        )

        meteora=meta.get(
            "address"
        )

        if not (
            token
            and pump
            and meteora
            and meta.get(
                "token_x"
            )
            and meta.get(
                "token_y"
            )
        ):
            continue

        x=dict(
            row
        )

        x[
            "size_sol"
        ]=MICRO_SOL

        x[
            "micro_lamports"
        ]=MICRO_LAMPORTS

        x[
            "_oracle_hot_valid_until"
        ]=(
            now
            +max(
                0.0,
                hot_seconds-age
            )
        )

        rows.append(
            x
        )

    rows.sort(
        key=lambda x:
            float(
                (
                    x.get(
                        "lifecycle"
                    )
                    or {}
                ).get(
                    "seconds_since_last_seen",
                    1e18
                )
            )
    )

    return rows


def live_universe_rows(root):

    root=Path(root)

    watch_seconds=float(
        os.getenv(
            "ORACLE_INITIAL_DISCOVERY_SECONDS",
            "120"
        )
    )

    poll_seconds=float(
        os.getenv(
            "ORACLE_DISCOVERY_POLL_SECONDS",
            "2"
        )
    )

    hot_seconds=min(
        90.0,
        float(
            q80.q45.HOT
        )
    )

    _ensure_oracle_discovery(
        root,
        max(
            150.0,
            watch_seconds+30.0
        )
    )

    print(
        "[CONTINUOUS_DISCOVERY] "
        "source=MRIYA+PUMPSWAP_PROGRAM "
        "initial_window=%.1fs "
        "hot_max_age=%.1fs "
        "replenishment=CONTINUOUS"%(
            watch_seconds,
            hot_seconds
        ),
        flush=True
    )

    deadline=(
        time.monotonic()
        +watch_seconds
    )

    last_status=0.0

    while (
        time.monotonic()
        <deadline
    ):

        recent=_recent_mriya_count(
            hot_seconds
        )

        if recent:

            rows=refresh_live_universe_rows(
                root
            )

            if rows:

                print(
                    "[INITIAL_FRESH_UNIVERSE] "
                    "recent_discovery=%d "
                    "hot_exact_bound=%d "
                    "youngest_age=%.3fs"%(
                        len(recent),
                        len(rows),
                        recent[0][1]
                    ),
                    flush=True
                )

                for row in rows:

                    life=(
                        row.get(
                            "lifecycle"
                        )
                        or {}
                    )

                    print(
                        "[FRESH_ROW] "
                        "token=%s "
                        "age=%.3fs "
                        "pump=%s "
                        "meteora=%s"%(
                            row[
                                "token"
                            ][:10],

                            float(
                                life.get(
                                    "seconds_since_last_seen",
                                    0.0
                                )
                            ),

                            row[
                                "pump_pool"
                            ][:12],

                            row[
                                "meteora_meta"
                            ][
                                "address"
                            ][:12],
                        ),
                        flush=True
                    )

                return rows

        elapsed=(
            watch_seconds
            -max(
                0.0,
                deadline
                -time.monotonic()
            )
        )

        if (
            elapsed-last_status
            >=10.0
        ):

            print(
                "[FRESH_WAIT] "
                "elapsed=%.1fs "
                "recent_mriya_tokens=%d"%(
                    elapsed,
                    len(recent)
                ),
                flush=True
            )

            last_status=elapsed

        time.sleep(
            min(
                poll_seconds,
                max(
                    0.0,
                    deadline
                    -time.monotonic()
                )
            )
        )

    print(
        "[DISCOVERY_HOLD] "
        "no fresh exact-bound "
        "PumpSwap->Meteora candidate",
        flush=True
    )

    return []

atexit.register(
    _stop_oracle_discovery
)

def run(
    mode="LIVE",
    seconds=120,
    scan_seconds=3.0
):
    mode=str(mode).upper()

    if mode not in (
        "PAPER",
        "LIVE"
    ):
        raise RuntimeError(
            "MODE_MUST_BE_PAPER_OR_LIVE"
        )

    root=Path.cwd()

    kp,user=base.require_keypair()

    if mode=="LIVE":
        base.require_arm()

    balance=int(
        rpc(
            "getBalance",
            [
                user,
                {
                    "commitment":
                        "confirmed"
                }
            ]
        )["value"]
    )

    print(
        "[ORACLE-007] "
        "UNIFIED PHYSICAL EXECUTION",
        flush=True
    )

    print(
        "[MODE] %s"%mode,
        flush=True
    )

    print(
        "[OWNER] ORACLE "
        "execution_authority=%s"%(
            "TRUE"
            if mode=="LIVE"
            else "FALSE"
        ),
        flush=True
    )

    print(
        "[WALLET] %s"%user,
        flush=True
    )

    print(
        "[BALANCE] %.9f SOL"%(
            balance/1e9
        ),
        flush=True
    )

    print(
        "[CAP] exact=0.001000000_SOL",
        flush=True
    )

    print(
        "[CONTRACT] PAPER_AND_LIVE="
        "IDENTICAL_SIGNED_PACKET",
        flush=True
    )

    print(
        "[ALT] create_new=FALSE "
        "reuse_existing_only=TRUE",
        flush=True
    )

    rows=live_universe_rows(
        root
    )

    if not rows:
        print(
            "[ORACLE_HOLD] "
            "NO_CURRENT_BOUND_PUMP_METEORA_UNIVERSE",
            flush=True
        )

        return 2

    deadline=(
        time.monotonic()
        +min(
            max(
                int(seconds),
                1
            ),
            120
        )
    )

    sends=0
    confirmed=0
    rejects=0
    hunt_round=0

    admission_refresh_seconds=float(
        os.getenv(
            "ORACLE_ADMISSION_REFRESH_SECONDS",
            "10"
        )
    )

    next_admission_refresh=0.0

    row_map={
        row["token"]:
            row
        for row in rows
    }

    while (
        time.monotonic()
        <deadline
    ):
        hunt_round+=1

        now_mono=time.monotonic()
        now_epoch=time.time()

        # ----------------------------------------------------
        # CONTINUOUS REPLENISHMENT
        # ----------------------------------------------------

        if (
            now_mono
            >=next_admission_refresh
        ):

            incoming=(
                refresh_live_universe_rows(
                    root
                )
            )

            admitted=0
            refreshed=0

            for row in incoming:

                token=row[
                    "token"
                ]

                if token in row_map:
                    refreshed+=1
                else:
                    admitted+=1

                # Replace with newest current binding/freshness
                # data for that token.
                row_map[
                    token
                ]=row

            next_admission_refresh=(
                now_mono
                +max(
                    5.0,
                    admission_refresh_seconds
                )
            )

            print(
                "[ROLLING_ADMISSION] "
                "incoming=%d "
                "new=%d "
                "refreshed=%d "
                "tracked=%d"%(
                    len(incoming),
                    admitted,
                    refreshed,
                    len(row_map)
                ),
                flush=True
            )

        # ----------------------------------------------------
        # AGE OUT ONLY TOKENS WHOSE CURRENT OBSERVATION EXPIRED
        # ----------------------------------------------------

        expired=[]

        for token,row in list(
            row_map.items()
        ):

            if float(
                row.get(
                    "_oracle_hot_valid_until",
                    0.0
                )
            ) <=now_epoch:

                expired.append(
                    token
                )

                row_map.pop(
                    token,
                    None
                )

        for token in expired:

            print(
                "[HOT_EXPIRE] "
                "token=%s"%(
                    token[:10]
                ),
                flush=True
            )

        rows=list(
            row_map.values()
        )

        # New Mriya candidates may arrive after every prior
        # candidate expires. Do NOT terminate the hunt merely
        # because the current active set is temporarily empty.
        if not rows:

            print(
                "[HUNT_EMPTY] "
                "round=%d "
                "waiting_for_replenishment=True"%(
                    hunt_round
                ),
                flush=True
            )

            time.sleep(
                min(
                    3.0,
                    max(
                        0.0,
                        deadline
                        -time.monotonic()
                    )
                )
            )

            continue

        print(
            "[HUNT_ROUND] "
            "round=%d "
            "active=%d "
            "tracked=%d"%(
                hunt_round,
                len(rows),
                len(row_map)
            ),
            flush=True
        )
        prepared=[]

        for row in rows:

            result=prepare_exact_packet(
                root,
                row,
                kp,
                user
            )

            if not result.get(
                "ok"
            ):
                rejects+=1

                reason=result.get(
                    "reason"
                )

                print(
                    "[PHYSICAL_REJECT] "
                    "token=%s reason=%s"%(
                        row[
                            "token"
                        ][:10],
                        reason
                    ),
                    flush=True
                )

                sim=result.get(
                    "simulation"
                ) or {}

                for line in (
                    sim.get("logs")
                    or []
                )[-6:]:
                    print(
                        "[SIM_LOG] "
                        +str(line),
                        flush=True
                    )

                continue

            prepared.append(
                result
            )

        if not prepared:
            remaining_hot=max(
                0.0,
                max(
                    float(
                        row.get(
                            "_oracle_hot_valid_until",
                            time.time()
                        )
                    )
                    for row in rows
                )
                -time.time()
            )

            print(
                "[HUNT_HOLD] "
                "round=%d "
                "no_executable_now=True "
                "remaining_hot=%.1fs "
                "next_reprice=%.1fs"%(
                    hunt_round,
                    remaining_hot,
                    max(
                        3.0,
                        float(
                            scan_seconds
                        )
                    )
                ),
                flush=True
            )

            sleep_for=min(
                max(
                    3.0,
                    float(
                        scan_seconds
                    )
                ),
                max(
                    0.0,
                    deadline
                    -time.monotonic()
                )
            )

            if sleep_for<=0:
                continue

            time.sleep(
                sleep_for
            )

            continue

        prepared.sort(
            key=lambda x:
                x[
                    "fresh_net_lamports"
                ],
            reverse=True
        )

        top=prepared[0]

        route=top["route"]

        print(
            "[PHYSICAL_PASS] "
            "token=%s "
            "bps=%+.2f "
            "net=%+.9f_SOL "
            "bytes=%d "
            "pump_min=%d "
            "pump_net=%d "
            "meteora_depth=%d"%(
                top[
                    "token"
                ][:10],

                top[
                    "fresh_bps"
                ],

                top[
                    "fresh_net_lamports"
                ]/1e9,

                top[
                    "bytes"
                ],

                route[
                    "pump_minimum_out"
                ],

                route[
                    "pump_spendable_out"
                ],

                route[
                    "meteora_bin_depth"
                ],
            ),
            flush=True
        )

        append({
            "event":
                "EXACT_PACKET_CERTIFIED",

            "mode":
                mode,

            "token":
                top["token"],

            "bytes":
                top["bytes"],

            "bps":
                top[
                    "fresh_bps"
                ],

            "net_lamports":
                top[
                    "fresh_net_lamports"
                ],

            "pump_minimum_out":
                route[
                    "pump_minimum_out"
                ],

            "pump_spendable_out":
                route[
                    "pump_spendable_out"
                ],

            "unix":
                time.time(),
        })

        if mode=="PAPER":
            print(
                "[PAPER_CERTIFIED] "
                "same_packet_ready_for_live=TRUE",
                flush=True
            )

            return 0

        # ----------------------------------------------------
        # LIVE BROADCASTS THE SAME RAW BYTES THAT JUST PASSED
        # SIGNED SIMULATION.
        # NO REBUILD. NO REQUOTE. NO ALTERATION.
        # ----------------------------------------------------

        base.require_arm()

        signature=base.send_once(
            top["raw"]
        )

        sends+=1

        print(
            "[LIVE_SENT] "
            "signature=%s"%signature,
            flush=True
        )

        tx=base.wait_confirmed(
            signature,
            deadline
        )

        if tx is None:
            print(
                "[HARD_STOP] "
                "confirmation_unknown",
                flush=True
            )

            return 3

        rec=base.reconcile(
            signature,
            tx,
            user,
            top["token"]
        )

        append({
            "event":
                "LIVE_RECONCILED",

            **rec,

            "unix":
                time.time(),
        })

        if (
            rec[
                "transaction_error"
            ]
            is not None
        ):
            print(
                "[HARD_STOP] "
                "confirmed_error=%s"%(
                    rec[
                        "transaction_error"
                    ]
                ),
                flush=True
            )

            return 4

        confirmed+=1

        print(
            "[LIVE_RECONCILED] "
            "signature=%s "
            "wallet_delta=%+.9f_SOL "
            "fee=%d "
            "token_residue=%d "
            "wsol_residue=%d "
            "clean=%s"%(
                signature,

                rec[
                    "wallet_delta_sol"
                ],

                rec[
                    "fee_lamports"
                ],

                rec[
                    "target_token_delta_raw"
                ],

                rec[
                    "wsol_delta_raw"
                ],

                rec[
                    "residue_clean"
                ],
            ),
            flush=True
        )

        # First physical cutover:
        # exactly ONE confirmed real transaction.
        print(
            "[ORACLE-007] "
            "FIRST_LIVE_CANARY_COMPLETE",
            flush=True
        )

        save({
            "revision":
                "ORACLE_003",

            "status":
                "LIVE_CONFIRMED",

            "execution_owner":
                "ORACLE",

            "sends":
                sends,

            "confirmed":
                confirmed,

            "last_signature":
                signature,

            "wallet_delta_sol":
                rec[
                    "wallet_delta_sol"
                ],

            "residue_clean":
                rec[
                    "residue_clean"
                ],
        })

        return 0

    save({
        "revision":
            "ORACLE_003",

        "status":
            "NO_PHYSICAL_PACKET_PASSED",

        "execution_owner":
            "ORACLE",

        "sends":
            sends,

        "confirmed":
            confirmed,

        "rejects":
            rejects,
    })

    print(
        "[ORACLE-007] COMPLETE "
        "sends=%d confirmed=%d "
        "rejects=%d"%(
            sends,
            confirmed,
            rejects
        ),
        flush=True
    )

    return 2
