from __future__ import annotations

import argparse
import base64
import json
import os
import time
import urllib.request
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_095_micro_capital_exact_size_shadow_probe as q95
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_092_just_in_time_execution_revalidation_gate as q92
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87


EXECUTION_OWNER="Q_SERIES"

MICRO_SOL=0.001
MICRO_LAMPORTS=1_000_000

MAX_RUNTIME_SECONDS=120
MAX_IN_FLIGHT=1
MAX_TX_BYTES=1232

LIVE_ARM_VALUE="I_ACCEPT_REAL_MONEY_RISK"
MICRO_ARM_VALUE="I_ACCEPT_0_001_SOL_TEST"

STATE=Path(
    "runtime_state/qseries/qarb_live_micro_execution/"
    "qarb_096_sequential_live_micro_executor.json"
)

LEDGER=Path(
    "runtime_state/qseries/qarb_live_micro_execution/"
    "qarb_096_live_micro_ledger.jsonl"
)

EXECUTION_AUTHORITY=True
ORACLE_EXECUTION_AUTHORITY=False


def _atomic(path,payload):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)

    tmp=p.with_suffix(p.suffix+".tmp")

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str
        ),
        encoding="utf-8"
    )

    tmp.replace(p)


def _append(path,payload):
    p=Path(path)
    p.parent.mkdir(parents=True,exist_ok=True)

    with p.open("a",encoding="utf-8") as f:
        f.write(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",",":"),
                default=str
            )
            +"\n"
        )


def _rpc(method,params,timeout=20):
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

    req=urllib.request.Request(
        url,
        data=body,
        headers={
            "content-type":"application/json",
            "user-agent":"qseries-qarb096/1.0",
        },
        method="POST"
    )

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

    return j.get("result")


def armed():
    return (
        os.getenv(
            "QSB_LIVE_ARM",
            ""
        )==LIVE_ARM_VALUE
        and
        os.getenv(
            "QSB_QARB096_ARM",
            ""
        )==MICRO_ARM_VALUE
    )


def require_arm():
    if not armed():
        raise RuntimeError(
            "QARB096_LIVE_NOT_ARMED"
        )


def require_keypair():
    # Reads locally from environment.
    # Secret is never printed or persisted.
    kp=q87.c.keypair()
    return kp,str(kp.pubkey())


def load_micro_rows(root):
    p=Path(root)/q95.MICRO_BINDINGS

    if not p.is_file():
        raise RuntimeError(
            "QARB095_MICRO_BINDINGS_MISSING"
        )

    d=json.loads(
        p.read_text(
            encoding="utf-8"
        )
    )

    if d.get("status")!="PASS":
        raise RuntimeError(
            "QARB095_NOT_PASS"
        )

    if int(
        d.get(
            "micro_test_lamports",
            0
        )
    )!=MICRO_LAMPORTS:
        raise RuntimeError(
            "MICRO_CAP_DRIFT"
        )

    rows=d.get("rows") or []

    if not rows:
        raise RuntimeError(
            "NO_MICRO_ROWS"
        )

    out=[]

    for x in rows:
        y=dict(x)

        if int(
            y.get(
                "micro_lamports",
                0
            )
        )!=MICRO_LAMPORTS:
            raise RuntimeError(
                "ROW_MICRO_CAP_DRIFT"
            )

        y["size_sol"]=MICRO_SOL

        out.append(y)

    return out


def hydration_binding(row):
    return {
        "token":
            row["token"],

        "pump_pool":
            row["pump_pool"],

        "meteora_meta":
            row["meteora_meta"],

        "size_sol":
            MICRO_SOL,
    }


def hydrate_rows(root,rows):
    bindings=[
        hydration_binding(x)
        for x in rows
    ]

    pairs,_=q87.q86.hydrate(
        root,
        bindings
    )

    return {
        p.token:p
        for p in pairs
    }


def native_live_route(
    user,
    pair,
    size_sol
):
    start=int(
        round(
            float(size_sol)
            *1_000_000_000
        )
    )

    if start!=MICRO_LAMPORTS:
        raise RuntimeError(
            "LIVE_NATIVE_SIZE_DRIFT"
        )

    # Current PumpSwap SDK path:
    # live swapSolanaState
    # -> quote-input autocomplete
    # -> matching instructions.
    p_ixs,pump_out=(
        q87.las.q59.native_pump_buy_ixs(
            user,
            pair.pump_pool,
            start
        )
    )

    pump_out=int(pump_out)

    if pump_out<=0:
        raise RuntimeError(
            "NATIVE_PUMP_OUTPUT_ZERO"
        )

    pump_indexes=[
        i
        for i,x in enumerate(p_ixs)
        if x.get("programId")==q87.c.PUMP
    ]

    if len(pump_indexes)!=1:
        raise RuntimeError(
            "NATIVE_PUMP_PROGRAM_IX_COUNT:"
            +str(len(pump_indexes))
        )

    pump_ix=p_ixs[
        pump_indexes[0]
    ]

    if not any(
        a.get("pubkey")==pair.pump_pool
        for a in (
            pump_ix.get("accounts")
            or []
        )
    ):
        raise RuntimeError(
            "NATIVE_PUMP_BINDING_DRIFT"
        )

    # Meteora is priced from the exact output produced
    # by the current Pump SDK quote, not an old local
    # constant-product approximation.
    quote=q87.exact_quote(
        pair,
        pump_out
    )

    meteora_ix=(
        q87.las.q59.dlmm_reverse_ix(
            user,
            q87.bound_meta(pair),
            pump_out,
            quote
        )
    )

    end=int(
        quote["raw_out"]
    )

    net=end-start

    bps=(
        net
        /start
        *10000.0
    )

    raw_candidates=(
        q87.las.q59
        .candidate_instruction_sets(
            p_ixs,
            meteora_ix
        )
    )

    # LIVE policy:
    # preserve exact SDK instructions.
    #
    # Do NOT use Q87 optional Pump-account trimming
    # for the native live route.
    #
    # Also reject the helper-stripped
    # PUMP_METEORA_ONLY shell.
    live_candidates=[]

    for name,ixs in raw_candidates:

        if "PUMP_METEORA_ONLY" in str(name):
            continue

        live_candidates.append({
            "name":str(name),
            "instructions":
                list(ixs),
            "pump_optional_removed":
                0,
        })

    if not live_candidates:
        raise RuntimeError(
            "NO_NATIVE_HELPER_PRESERVING_CANDIDATES"
        )

    return {
        "token":
            pair.token,

        "start_lamports":
            start,

        "pump_token_out_raw":
            pump_out,

        "meteora_end_lamports":
            end,

        "pre_sim_net_lamports":
            net,

        "pre_sim_bps":
            bps,

        "quote_source":
            "PUMP_NATIVE_SDK_LIVE_STATE"
            "_TO_METEORA_EXACT",

        "bins_crossed":
            int(
                quote.get(
                    "bins_crossed",
                    1
                )
            ),

        "pump_ixs":
            p_ixs,

        "pump_ix":
            pump_ix,

        "meteora_ix":
            meteora_ix,

        # Native builder gives us concrete instructions;
        # no Pump API transaction ALT dependency exists.
        "base_alts":
            [],

        "live_candidates":
            live_candidates,
    }


def fresh_candidates(root,rows,user):
    pair_map=hydrate_rows(
        root,
        rows
    )

    found=[]

    for row in rows:
        pair=pair_map.get(
            row["token"]
        )

        if pair is None:
            continue

        try:
            route=native_live_route(
                user,
                pair,
                MICRO_SOL
            )

        except Exception as exc:
            print(
                "[NATIVE_REJECT] "
                "token=%s error=%s:%s"%(
                    row["token"][:10],
                    type(exc).__name__,
                    exc,
                ),
                flush=True
            )
            continue

        if int(
            route.get(
                "start_lamports",
                -1
            )
        )!=MICRO_LAMPORTS:
            continue

        net=int(
            route[
                "pre_sim_net_lamports"
            ]
        )

        bps=float(
            route[
                "pre_sim_bps"
            ]
        )

        if net<=0:
            continue

        if (
            bps
            <q87.las.q59.MIN_NET_BPS
        ):
            continue

        found.append({
            "row":
                row,

            "pair":
                pair,

            "route":
                route,

            "bps":
                bps,

            "net_lamports":
                net,

            "pump_out_raw":
                int(
                    route[
                        "pump_token_out_raw"
                    ]
                ),

            "quote_source":
                route[
                    "quote_source"
                ],
        })

    found.sort(
        key=lambda x:
            (
                x["net_lamports"],
                x["bps"]
            ),
        reverse=True
    )

    return found



def _qarb096_alt_state_path(root):
    return (
        Path(root)
        /"runtime_state/qseries/"
         "qarb_execution_engineering/"
         "qarb_096_micro_alt.json"
    )


def _alt_key(token):
    return str(token)


def _load_alt_state(root):
    p=_qarb096_alt_state_path(
        root
    )

    if not p.is_file():
        return {
            "revision":
                "QARB_096_MICRO_ALT",

            "tables":{},
        }

    try:
        d=json.loads(
            p.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            d.get("tables"),
            dict
        ):
            d["tables"]={}

        return d

    except Exception:
        return {
            "revision":
                "QARB_096_MICRO_ALT",

            "tables":{},
        }


def _saved_alt(root,token):
    state=_load_alt_state(
        root
    )

    row=state[
        "tables"
    ].get(
        _alt_key(token)
    )

    if not isinstance(row,dict):
        return None

    address=row.get(
        "address"
    )

    if not address:
        return None

    try:
        got=_rpc(
            "getAccountInfo",
            [
                address,
                {
                    "encoding":"base64",
                    "commitment":"confirmed"
                }
            ]
        )

        if not isinstance(got,dict):
            return None

        value=got.get("value")

        if not isinstance(value,dict):
            return None

        if not value.get("data"):
            return None

    except Exception:
        return None

    return address


def _apply_saved_alt(
    root,
    route
):
    token=route.get(
        "token"
    )

    if not token:
        return route

    alt=_saved_alt(
        root,
        token
    )

    if not alt:
        return route

    print(
        "[ALT_REUSE] token=%s address=%s"%(
            str(token)[:10],
            alt,
        ),
        flush=True
    )

    route=dict(route)

    route["base_alts"]=[
        alt
    ]

    route[
        "qarb096_micro_alt"
    ]=alt

    return route


def _oversize_only(result):
    attempts=(
        result.get("attempts")
        or []
    )

    seen=False

    for row in attempts:
        for ca in (
            row.get(
                "compile_attempts"
            )
            or []
        ):
            err=str(
                ca.get(
                    "error",
                    ""
                )
            )

            if not err:
                continue

            if err.startswith(
                "ATOMIC_TX_TOO_LARGE:"
            ):
                seen=True
                continue

            return False

    return seen


def _alt_addresses_from_route(
    route,
    user
):
    candidates=(
        route.get(
            "live_candidates"
        )
        or []
    )

    if not candidates:
        raise RuntimeError(
            "ALT_NO_LIVE_CANDIDATE"
        )

    # FULL preserves every instruction.
    full=next(
        (
            x
            for x in candidates
            if x.get("name")=="FULL"
        ),
        candidates[0]
    )

    ixs=full[
        "instructions"
    ]

    program_ids={
        str(
            x.get(
                "programId",
                ""
            )
        )
        for x in ixs
    }

    out=[]
    seen=set()

    for ix in ixs:
        for a in (
            ix.get("accounts")
            or []
        ):
            pub=str(
                a.get(
                    "pubkey",
                    ""
                )
            )

            if not pub:
                continue

            if pub==str(user):
                continue

            if pub in program_ids:
                continue

            if bool(
                a.get("isSigner")
            ):
                continue

            if pub in seen:
                continue

            seen.add(pub)
            out.append(pub)

    # Four addresses are enough to recover roughly
    # the missing 74 bytes; keep eight for margin.
    out=out[:8]

    if len(out)<4:
        raise RuntimeError(
            "ALT_TOO_FEW_ELIGIBLE_ADDRESSES:"
            +str(len(out))
        )

    return out


def _build_alt_setup(
    user,
    addresses
):
    import shutil
    import subprocess

    node=shutil.which(
        "node"
    )

    if node is None:
        raise RuntimeError(
            "NODE_MISSING_FOR_ALT"
        )

    recent_slot=int(
        _rpc(
            "getSlot",
            [{
                "commitment":
                    "finalized"
            }]
        )
    )

    d=(
        Path.cwd()
        /"qseries_v2/"
         "oracle_strategy_intelligence/"
         "solana_money/"
         "qsb059d_pump_native"
    )

    req={
        "user":
            str(user),

        "recentSlot":
            recent_slot,

        "addresses":
            addresses,
    }

    p=subprocess.run(
        [
            node,
            "build_qarb096_alt_ix.mjs"
        ],
        cwd=d,
        input=json.dumps(req),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30
    )

    if p.returncode!=0:
        raise RuntimeError(
            "ALT_NODE_FAILED:"
            +p.stderr[-2000:]
        )

    try:
        j=json.loads(
            p.stdout.strip()
            .splitlines()[-1]
        )

    except Exception:
        raise RuntimeError(
            "ALT_BAD_JSON:"
            +p.stdout[-2000:]
        )

    if not j.get("ok"):
        raise RuntimeError(
            "ALT_BUILD_FAILED:"
            +str(
                j.get("reason")
            )
        )

    return j


def bootstrap_micro_alt(
    root,
    row,
    kp,
    user,
    deadline
):
    token=row["token"]

    existing=_saved_alt(
        root,
        token
    )

    if existing:
        return {
            "ok":True,
            "created":False,
            "address":existing,
        }

    pair_map=hydrate_rows(
        root,
        [row]
    )

    pair=pair_map.get(
        token
    )

    if pair is None:
        return {
            "ok":False,
            "reason":"PAIR_MISSING",
        }

    try:
        route=native_live_route(
            user,
            pair,
            MICRO_SOL
        )

        addresses=(
            _alt_addresses_from_route(
                route,
                user
            )
        )

        setup=_build_alt_setup(
            user,
            addresses
        )

    except Exception as exc:
        return {
            "ok":False,

            "reason":
                "ALT_SETUP_BUILD:"
                +type(exc).__name__
                +":"
                +str(exc),
        }

    bh=_rpc(
        "getLatestBlockhash",
        [{
            "commitment":
                "confirmed"
        }]
    )["value"]["blockhash"]

    try:
        msg,unsigned=(
            q87.c.compile_v0(
                user,
                setup[
                    "instructions"
                ],
                [],
                bh
            )
        )

    except Exception as exc:
        return {
            "ok":False,

            "reason":
                "ALT_SETUP_COMPILE:"
                +str(exc),
        }

    raw=q87.c.signed_tx(
        msg,
        kp
    )

    if len(raw)>MAX_TX_BYTES:
        return {
            "ok":False,

            "reason":
                "ALT_SETUP_TOO_LARGE:"
                +str(len(raw)),
        }

    sim=signed_simulation(
        raw
    )

    if sim.get("err") is not None:
        return {
            "ok":False,

            "reason":
                "ALT_SETUP_SIM_ERROR:"
                +str(
                    sim.get("err")
                ),

            "simulation":
                sim,
        }

    if time.monotonic()>=deadline:
        return {
            "ok":False,
            "reason":
                "ALT_SETUP_WINDOW_CLOSED",
        }

    # Same explicit session arm governs this
    # one-time Q Series infrastructure transaction.
    require_arm()

    before=int(
        _rpc(
            "getBalance",
            [
                str(user),
                {
                    "commitment":
                        "confirmed"
                }
            ]
        )["value"]
    )

    signature=send_once(
        raw
    )

    tx=wait_confirmed(
        signature,
        deadline
    )

    if tx is None:
        return {
            "ok":False,

            "reason":
                "ALT_CONFIRMATION_UNKNOWN",

            "hard_stop":
                True,

            "signature":
                signature,
        }

    err=(
        tx.get(
            "meta",
            {}
        )
        or {}
    ).get(
        "err"
    )

    if err is not None:
        return {
            "ok":False,

            "reason":
                "ALT_CONFIRMED_ERROR:"
                +str(err),

            "signature":
                signature,
        }

    after=int(
        _rpc(
            "getBalance",
            [
                str(user),
                {
                    "commitment":
                        "confirmed"
                }
            ]
        )["value"]
    )

    state=_load_alt_state(
        root
    )

    state[
        "tables"
    ][
        _alt_key(token)
    ]={
        "address":
            setup[
                "lookupTable"
            ],

        "addresses":
            setup[
                "addresses"
            ],

        "recent_slot":
            setup[
                "recentSlot"
            ],

        "signature":
            signature,

        "wallet_delta_lamports":
            after-before,

        "created_unix":
            time.time(),
    }

    _atomic(
        _qarb096_alt_state_path(
            root
        ),
        state
    )

    alt=setup[
        "lookupTable"
    ]

    setup_slot=int(
        tx.get(
            "slot",
            0
        )
        or 0
    )

    # Address lookup tables become usable after the slot in
    # which they were created/extended. The setup transaction
    # has already been confirmed above.
    while time.monotonic()<deadline:

        try:
            slot=int(
                _rpc(
                    "getSlot",
                    [{
                        "commitment":
                            "confirmed"
                    }]
                )
            )

            got=_rpc(
                "getAccountInfo",
                [
                    alt,
                    {
                        "encoding":"base64",
                        "commitment":"confirmed"
                    }
                ]
            )

            value=(
                got.get("value")
                if isinstance(got,dict)
                else None
            )

            if (
                setup_slot>0
                and slot>setup_slot
                and isinstance(
                    value,
                    dict
                )
                and value.get("data")
            ):
                return {
                    "ok":True,

                    "created":True,

                    "address":
                        alt,

                    "signature":
                        signature,

                    "wallet_delta_lamports":
                        after-before,

                    "addresses":
                        len(
                            setup[
                                "addresses"
                            ]
                        ),
                }

        except Exception:
            pass

        time.sleep(0.4)

    # The setup transaction was confirmed already. If the ALT
    # account itself now exists, preserve it and allow the NEXT
    # scan/session to reuse it instead of blindly creating a
    # duplicate table.
    try:
        got=_rpc(
            "getAccountInfo",
            [
                alt,
                {
                    "encoding":"base64",
                    "commitment":"confirmed"
                }
            ]
        )

        if (
            isinstance(got,dict)
            and isinstance(
                got.get("value"),
                dict
            )
        ):
            return {
                "ok":True,

                "created":True,

                "address":
                    alt,

                "signature":
                    signature,

                "wallet_delta_lamports":
                    after-before,

                "addresses":
                    len(
                        setup[
                            "addresses"
                        ]
                    ),

                "activation_deferred":
                    True,
            }

    except Exception:
        pass

    return {
        "ok":False,

        "reason":
            "ALT_ACCOUNT_NOT_VISIBLE",

        "hard_stop":
            True,

        "signature":
            signature,
    }



def compile_signed(
    user,
    kp,
    route,
    preferred_name
):
    bh=_rpc(
        "getLatestBlockhash",
        [{
            "commitment":"confirmed"
        }]
    )["value"]["blockhash"]

    try:
        extra=(
            q87.las.q59
            .recent_mriya_alt_keys()
        )
    except Exception:
        extra=[]

    options=q87.alt_sets(
        route["base_alts"],
        extra
    )

    if route.get("live_candidates"):
        candidates=[
            dict(x)
            for x in route[
                "live_candidates"
            ]
        ]
    else:
        candidates=list(
            q87.repaired_candidates(
                route
            )
        )

    ordered=[]

    if preferred_name:
        ordered.extend(
            x
            for x in candidates
            if x.get("name")
            ==preferred_name
        )

    ordered.extend(
        x
        for x in candidates
        if x not in ordered
    )

    attempts=[]

    for candidate in ordered:

        name=str(
            candidate.get(
                "name",
                ""
            )
        )

        # LIVE RULE:
        # Never execute the helper-stripped Pump shell.
        # Q59 defines PUMP_METEORA_ONLY as [pump,m_ix],
        # which can omit required ATA/account preparation.
        if "PUMP_METEORA_ONLY" in name:
            attempts.append({
                "candidate":name,
                "compiled":False,
                "error":
                    "LIVE_REJECT_HELPER_STRIPPED_PUMP_SHELL",
            })
            continue

        comp=q87.compile_candidate(
            user,
            candidate[
                "instructions"
            ],
            options,
            bh
        )

        rec={
            "candidate":
                candidate["name"],
            "compiled":
                bool(
                    comp.get("ok")
                ),
            "compile_attempts":
                comp.get(
                    "attempts",
                    []
                ),
        }

        attempts.append(rec)

        if not comp.get("ok"):
            continue

        raw=q87.c.signed_tx(
            comp["msg"],
            kp
        )

        rec["bytes"]=len(raw)

        if len(raw)>MAX_TX_BYTES:
            rec["error"]="SIGNED_TOO_LARGE"
            continue

        return {
            "ok":True,
            "candidate":
                candidate["name"],
            "bytes":len(raw),
            "raw":raw,
            "attempts":attempts,
        }

    return {
        "ok":False,
        "reason":"NO_LEGAL_SIGNED_TX",
        "attempts":attempts,
    }


def signed_simulation(raw):
    result=_rpc(
        "simulateTransaction",
        [
            base64.b64encode(
                raw
            ).decode(),
            {
                "encoding":"base64",
                "sigVerify":True,
                "commitment":"processed",
                "replaceRecentBlockhash":False,
            }
        ]
    )

    if not isinstance(result,dict):
        raise RuntimeError(
            "SIMULATION_RESULT_MISSING"
        )

    value=result.get("value")

    if not isinstance(value,dict):
        raise RuntimeError(
            "SIMULATION_VALUE_MISSING"
        )

    return {
        "err":value.get("err"),
        "units":
            value.get(
                "unitsConsumed"
            ),
        "logs":
            value.get("logs") or [],
        "accounts":
            value.get("accounts"),
        "return_data":
            value.get("returnData"),
    }


def send_once(raw):
    # Q Series owns this call.
    # maxRetries=0 prevents automatic RPC resubmission.
    require_arm()

    return _rpc(
        "sendTransaction",
        [
            base64.b64encode(
                raw
            ).decode(),
            {
                "encoding":"base64",
                "skipPreflight":False,
                "preflightCommitment":
                    "processed",
                "maxRetries":0,
            }
        ]
    )


def get_confirmed(signature):
    return _rpc(
        "getTransaction",
        [
            signature,
            {
                "encoding":"jsonParsed",
                "commitment":"confirmed",
                "maxSupportedTransactionVersion":0,
            }
        ]
    )


def wait_confirmed(
    signature,
    deadline,
    timeout_seconds=20
):
    stop=min(
        float(deadline),
        time.monotonic()
        +float(timeout_seconds)
    )

    while time.monotonic()<stop:
        tx=get_confirmed(
            signature
        )

        if tx is not None:
            return tx

        time.sleep(0.8)

    return None


def _raw_token_amount(row):
    try:
        return int(
            (
                row.get(
                    "uiTokenAmount"
                )
                or {}
            ).get(
                "amount"
            )
            or 0
        )
    except Exception:
        return 0


def owner_mint_balances(
    rows,
    owner
):
    out={}

    for x in rows or []:
        if x.get("owner")!=owner:
            continue

        mint=x.get("mint")

        if not mint:
            continue

        out[mint]=(
            out.get(mint,0)
            +_raw_token_amount(x)
        )

    return out


def reconcile(
    signature,
    tx,
    user,
    token
):
    meta=(tx or {}).get(
        "meta"
    ) or {}

    pre=list(
        meta.get(
            "preBalances"
        ) or []
    )

    post=list(
        meta.get(
            "postBalances"
        ) or []
    )

    if not pre or not post:
        raise RuntimeError(
            "CONFIRMED_BALANCES_MISSING"
        )

    # QARB transaction compiler always places
    # payer first in static keys.
    payer_pre=int(pre[0])
    payer_post=int(post[0])

    fee=int(
        meta.get(
            "fee"
        ) or 0
    )

    wallet_delta=(
        payer_post
        -payer_pre
    )

    pre_tokens=owner_mint_balances(
        meta.get(
            "preTokenBalances"
        ),
        user
    )

    post_tokens=owner_mint_balances(
        meta.get(
            "postTokenBalances"
        ),
        user
    )

    token_delta=(
        post_tokens.get(token,0)
        -pre_tokens.get(token,0)
    )

    wsol_delta=(
        post_tokens.get(
            q87.c.WSOL,
            0
        )
        -pre_tokens.get(
            q87.c.WSOL,
            0
        )
    )

    clean_residue=(
        token_delta==0
        and wsol_delta==0
    )

    # wallet_delta already includes fee.
    # Do NOT subtract fee again.
    return {
        "signature":
            signature,

        "transaction_error":
            meta.get("err"),

        "fee_lamports":
            fee,

        "payer_pre_lamports":
            payer_pre,

        "payer_post_lamports":
            payer_post,

        "wallet_delta_lamports":
            wallet_delta,

        "wallet_delta_sol":
            wallet_delta/1e9,

        "route_delta_before_fee_lamports":
            wallet_delta+fee,

        "target_token_delta_raw":
            token_delta,

        "wsol_delta_raw":
            wsol_delta,

        "residue_clean":
            clean_residue,

        "confirmed_slot":
            tx.get("slot"),

        "execution_owner":
            EXECUTION_OWNER,
    }


def final_prepare(
    root,
    row,
    kp,
    user
):
    pair_map=hydrate_rows(
        root,
        [row]
    )

    pair=pair_map.get(
        row["token"]
    )

    if pair is None:
        return {
            "ok":False,
            "reason":"PAIR_MISSING",
        }

    try:
        route=native_live_route(
            user,
            pair,
            MICRO_SOL
        )

    except Exception as exc:
        return {
            "ok":False,
            "reason":
                "NATIVE_EXECUTABLE_QUOTE_ERROR:"
                +type(exc).__name__
                +":"
                +str(exc),
        }

    route=_apply_saved_alt(
        root,
        route
    )

    if int(
        route.get(
            "start_lamports",
            -1
        )
    )!=MICRO_LAMPORTS:
        return {
            "ok":False,
            "reason":
                "MICRO_CAP_DRIFT",
        }

    net=int(
        route[
            "pre_sim_net_lamports"
        ]
    )

    bps=float(
        route[
            "pre_sim_bps"
        ]
    )

    if net<=0:
        return {
            "ok":False,
            "reason":
                "NATIVE_NET_NONPOSITIVE",

            "fresh_net_lamports":
                net,

            "fresh_bps":
                bps,
        }

    if bps < q87.las.q59.MIN_NET_BPS:
        return {
            "ok":False,
            "reason":
                "NATIVE_BPS_BELOW_GATE",

            "fresh_net_lamports":
                net,

            "fresh_bps":
                bps,
        }

    # Do NOT prefer the old Q95 candidate name.
    # Q95 was generated from the legacy Pump route.
    compiled=compile_signed(
        user,
        kp,
        route,
        None
    )

    if not compiled.get("ok"):
        return compiled

    sim=signed_simulation(
        compiled["raw"]
    )

    if sim.get("err") is not None:
        logs=sim.get(
            "logs"
        ) or []

        tail=logs[-6:]

        return {
            "ok":False,

            "reason":
                "SIGNED_SIM_ERROR:"
                +str(
                    sim.get("err")
                ),

            "simulation":
                sim,

            "simulation_log_tail":
                tail,

            "fresh_net_lamports":
                net,

            "fresh_bps":
                bps,
        }

    return {
        "ok":True,

        "fresh_net_lamports":
            net,

        "fresh_bps":
            bps,

        "pump_token_out_raw":
            int(
                route[
                    "pump_token_out_raw"
                ]
            ),

        "quote_source":
            route[
                "quote_source"
            ],

        "candidate":
            compiled[
                "candidate"
            ],

        "bytes":
            compiled["bytes"],

        "raw":
            compiled["raw"],

        "simulation":
            sim,
    }


def run(
    root=None,
    seconds=120,
    scan_seconds=2.0
):
    root=Path(
        root or Path.cwd()
    )

    seconds=min(
        max(
            1,
            int(seconds)
        ),
        MAX_RUNTIME_SECONDS
    )

    require_arm()

    kp,user=require_keypair()

    rows=load_micro_rows(
        root
    )

    start=time.monotonic()
    deadline=start+seconds

    sends=0
    confirmed=0
    rejected=0
    skipped=0

    state={
        "revision":"QARB_096",
        "status":"RUNNING",
        "execution_owner":
            EXECUTION_OWNER,
        "oracle_execution_authority":
            False,
        "live_micro_cap_sol":
            MICRO_SOL,
        "live_micro_cap_lamports":
            MICRO_LAMPORTS,
        "runtime_seconds":
            seconds,
        "max_in_flight":
            1,
        "production_sizes_mutated":
            False,
        "sends":0,
        "confirmed":0,
        "started_unix":
            time.time(),
    }

    _atomic(
        root/STATE,
        state
    )

    print(
        "[QARB-096] 120-SECOND "
        "SEQUENTIAL LIVE MICRO EXECUTOR",
        flush=True
    )

    print(
        "[OWNER] execution_owner=Q_SERIES "
        "oracle_execution_authority=FALSE",
        flush=True
    )

    print(
        "[CAP] exact_per_transaction="
        "0.001000_SOL",
        flush=True
    )

    print(
        "[SEQUENTIAL] max_in_flight=1 "
        "no_send_retry=TRUE",
        flush=True
    )

    print(
        "[PRESERVE] production "
        "0.28/1.4 SOL sizing unchanged",
        flush=True
    )

    print(
        "[WALLET] %s"%user,
        flush=True
    )

    while time.monotonic()<deadline:

        try:
            candidates=fresh_candidates(
                root,
                rows,
                user
            )

        except Exception as exc:
            print(
                "[SCAN_HOLD] %s:%s"%(
                    type(exc).__name__,
                    exc
                ),
                flush=True
            )

            time.sleep(
                min(
                    scan_seconds,
                    max(
                        0,
                        deadline
                        -time.monotonic()
                    )
                )
            )

            continue

        if not candidates:
            print(
                "[SCAN] no current "
                "0.001 SOL route",
                flush=True
            )

            time.sleep(
                min(
                    scan_seconds,
                    max(
                        0,
                        deadline
                        -time.monotonic()
                    )
                )
            )

            continue

        top=candidates[0]
        row=top["row"]

        # Q Series automatically selected this opportunity.
        # No operator interaction occurs before final JIT preparation.

        final=final_prepare(
            root,
            row,
            kp,
            user
        )

        if (
            not final.get("ok")
            and final.get("reason")
                =="NO_LEGAL_SIGNED_TX"
            and _oversize_only(final)
        ):
            print(
                "[ALT_COMPACTION] "
                "token=%s packet_oversize=TRUE "
                "preserving_all_helpers=TRUE"%(
                    row["token"][:10],
                ),
                flush=True
            )

            alt_result=bootstrap_micro_alt(
                root,
                row,
                kp,
                user,
                deadline
            )

            if alt_result.get("ok"):
                print(
                    "[ALT_READY] "
                    "token=%s address=%s "
                    "created=%s setup_delta=%s"%(
                        row["token"][:10],
                        alt_result.get(
                            "address"
                        ),
                        alt_result.get(
                            "created"
                        ),
                        alt_result.get(
                            "wallet_delta_lamports"
                        ),
                    ),
                    flush=True
                )

                # Full price/state refresh AFTER
                # the ALT is physically active.
                final=final_prepare(
                    root,
                    row,
                    kp,
                    user
                )

            else:
                print(
                    "[ALT_REJECT] "
                    "token=%s reason=%s"%(
                        row["token"][:10],
                        alt_result.get(
                            "reason"
                        ),
                    ),
                    flush=True
                )

                if alt_result.get(
                    "hard_stop"
                ):
                    break

        if not final.get("ok"):
            rejected+=1

            rec={
                "event":
                    "FINAL_PRE_SEND_REJECT",

                "token":
                    row["token"],

                "reason":
                    final.get(
                        "reason"
                    ),

                "unix":
                    time.time(),

                "real_money_moved":
                    False,
            }

            _append(
                root/LEDGER,
                rec
            )

            print(
                "[FINAL_REJECT] "
                "token=%s reason=%s"%(
                    row["token"][:10],
                    final.get(
                        "reason"
                    ),
                ),
                flush=True
            )

            if final.get(
                "simulation_log_tail"
            ):
                for line in final[
                    "simulation_log_tail"
                ]:
                    print(
                        "[SIM_LOG] "+str(line),
                        flush=True
                    )

            continue

        print(
            "[SIGNED_SIM_PASS] "
            "token=%s "
            "fresh_bps=%+.2f "
            "bytes=%d "
            "units=%s"%(
                row["token"][:10],
                final["fresh_bps"],
                final["bytes"],
                final[
                    "simulation"
                ].get(
                    "units"
                ),
            ),
            flush=True
        )

        # Q Series autonomous execution boundary.
        #
        # The complete 120-second session was explicitly armed
        # before startup. No per-trade operator prompt is used.
        #
        # Re-check the arm at the exact broadcast boundary.
        if time.monotonic()>=deadline:
            print(
                "[WINDOW_CLOSED] "
                "transaction not broadcast",
                flush=True
            )
            break

        require_arm()

        print(
            "[AUTO_BROADCAST] "
            "token=%s "
            "principal=0.001000_SOL "
            "fresh_bps=%+.2f "
            "quote_net=%+.9f_SOL "
            "bytes=%d"%(
                row["token"][:10],
                final["fresh_bps"],
                final["fresh_net_lamports"]/1e9,
                final["bytes"],
            ),
            flush=True
        )

        signature=send_once(
            final["raw"]
        )

        sends+=1

        sent_record={
            "event":"LIVE_SENT",
            "sequence":sends,
            "signature":signature,
            "token":row["token"],
            "principal_lamports":
                MICRO_LAMPORTS,
            "principal_sol":
                MICRO_SOL,
            "fresh_quote_net_lamports":
                final[
                    "fresh_net_lamports"
                ],
            "fresh_quote_bps":
                final[
                    "fresh_bps"
                ],
            "candidate":
                final["candidate"],
            "transaction_bytes":
                final["bytes"],
            "unix":
                time.time(),
            "real_money_moved":
                True,
            "execution_owner":
                EXECUTION_OWNER,
        }

        _append(
            root/LEDGER,
            sent_record
        )

        print(
            "[LIVE_SENT] "
            "sequence=%d token=%s "
            "signature=%s"%(
                sends,
                row["token"][:10],
                signature,
            ),
            flush=True
        )

        tx=wait_confirmed(
            signature,
            deadline
        )

        if tx is None:
            # Unknown in-flight state:
            # NEVER permit another transaction.
            print(
                "[HARD_STOP] confirmation "
                "unknown; no second transaction",
                flush=True
            )

            _append(
                root/LEDGER,
                {
                    "event":
                        "CONFIRMATION_UNKNOWN_HARD_STOP",
                    "signature":
                        signature,
                    "unix":
                        time.time(),
                }
            )

            break

        rec=reconcile(
            signature,
            tx,
            user,
            row["token"]
        )

        _append(
            root/LEDGER,
            {
                "event":
                    "LIVE_RECONCILED",
                "sequence":
                    sends,
                **rec,
                "unix":
                    time.time(),
            }
        )

        if rec[
            "transaction_error"
        ] is not None:
            print(
                "[HARD_STOP] confirmed "
                "transaction error=%s"%(
                    rec[
                        "transaction_error"
                    ],
                ),
                flush=True
            )
            break

        confirmed+=1

        print(
            "[LIVE_RECONCILED] "
            "sequence=%d "
            "wallet_delta=%+.9f_SOL "
            "fee=%d_lamports "
            "token_residue=%d "
            "wsol_residue=%d "
            "clean=%s"%(
                sends,
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

        # Do not compound unknown residual assets
        # into another experimental trade.
        if not rec[
            "residue_clean"
        ]:
            print(
                "[HARD_STOP] nonzero "
                "intermediate residue",
                flush=True
            )
            break

        state.update({
            "sends":
                sends,
            "confirmed":
                confirmed,
            "last_signature":
                signature,
            "last_wallet_delta_sol":
                rec[
                    "wallet_delta_sol"
                ],
            "last_fee_lamports":
                rec[
                    "fee_lamports"
                ],
            "last_residue_clean":
                rec[
                    "residue_clean"
                ],
            "updated_unix":
                time.time(),
        })

        _atomic(
            root/STATE,
            state
        )

    state.update({
        "status":"COMPLETE",
        "sends":sends,
        "confirmed":confirmed,
        "pre_send_rejected":
            rejected,
        "automatic_session":True,
        "ended_unix":
            time.time(),
        "execution_owner":
            EXECUTION_OWNER,
        "oracle_execution_authority":
            False,
        "production_sizes_mutated":
            False,
    })

    _atomic(
        root/STATE,
        state
    )

    print(
        "[QARB-096] COMPLETE "
        "sends=%d confirmed=%d "
        "pre_send_rejected=%d "
        "skipped=%d "
        "automatic_session=TRUE"%(
            sends,
            confirmed,
            rejected,
            skipped,
        ),
        flush=True
    )

    print(
        "[PRESERVE] "
        "production_sizes_mutated=FALSE",
        flush=True
    )

    print(
        "[OWNER] execution_owner=Q_SERIES "
        "oracle_execution_authority=FALSE",
        flush=True
    )

    return 0


def main():
    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=int,
        default=120
    )

    ap.add_argument(
        "--scan-seconds",
        type=float,
        default=2.0
    )

    a=ap.parse_args()

    return run(
        Path.cwd(),
        seconds=a.seconds,
        scan_seconds=a.scan_seconds
    )


if __name__=="__main__":
    raise SystemExit(main())
