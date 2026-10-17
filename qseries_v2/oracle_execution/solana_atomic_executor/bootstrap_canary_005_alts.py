from __future__ import annotations

import argparse
import time
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
from qseries_v2.solana_live_execution import qarb_096_sequential_live_micro_executor as q96

EXECUTION_AUTHORITY=False
TRADE_BROADCAST=False
MAX_TX_BYTES=1232
ORIGINAL_Q96_RPC=q96._rpc


def _retry_rpc(
    method,
    params,
    timeout=20,
    attempts=5,
):
    # Broadcast remains single-shot. Never loop sendTransaction.
    if str(method)=="sendTransaction":
        return ORIGINAL_Q96_RPC(
            method,
            params,
            timeout,
        )

    last=None

    for attempt in range(
        1,
        int(attempts)+1,
    ):
        try:
            return ORIGINAL_Q96_RPC(
                method,
                params,
                timeout,
            )

        except Exception as exc:
            last=exc

            code=getattr(
                exc,
                "code",
                None,
            )

            is_429=(
                code==429
                or "429" in str(exc)
                or "Too Many Requests"
                in str(exc)
            )

            if (
                not is_429
                or attempt>=int(attempts)
            ):
                raise

            delay=min(
                8.0,
                0.75*(2**(attempt-1)),
            )

            print(
                "[CANARY_ALT_RPC_429] "
                "method=%s attempt=%d/%d "
                "sleep=%.2fs"
                %(
                    method,
                    attempt,
                    attempts,
                    delay,
                ),
                flush=True,
            )

            time.sleep(delay)

    raise RuntimeError(
        "CANARY_ALT_RPC_RETRY_EXHAUSTED:"
        +str(method)
        +":"
        +str(last)
    )


def _call_with_retry_rpc(
    func,
    *args,
    **kwargs,
):
    old=q96._rpc
    q96._rpc=_retry_rpc
    try:
        return func(
            *args,
            **kwargs,
        )
    finally:
        q96._rpc=old


def _initialize_ready(state,user):
    rt.READY_TOKENS.clear()
    rt.TEMPLATES.clear()
    rt.METEORA_TEMPLATES.clear()

    token_warm=rt.install_proven_hot_math(state)
    rt.prebuild_templates(state,user)
    rt.prebuild_meteora_templates(
        state,
        user,
        token_warm,
    )

    for pair in list(state.get("pairs") or []):
        token=str(pair.token)
        if token not in rt.READY_TOKENS:
            continue
        try:
            rt.q18.worker().warm(
                str(pair.pump_pool)
            )
        except Exception:
            rt.READY_TOKENS.discard(token)

    if not rt.READY_TOKENS:
        raise RuntimeError(
            "CANARY_ALT_NO_RUNTIME_READY_PAIRS"
        )

    return set(rt.READY_TOKENS)


def _local_saved_tokens(root):
    state=q96._load_alt_state(root)
    tables=state.get("tables") or {}
    return {
        str(token)
        for token,row in tables.items()
        if isinstance(row,dict)
        and row.get("address")
    }


def _select_current_pair(
    root,
    state,
    preferred_prefix=None,
):
    ready=set(rt.READY_TOKENS)

    pairs=[
        p for p in list(state.get("pairs") or [])
        if str(p.token) in ready
    ]

    if preferred_prefix:
        preferred=[
            p for p in pairs
            if str(p.token).startswith(
                str(preferred_prefix)
            )
        ]
        if len(preferred)==1:
            pairs=preferred
        elif len(preferred)>1:
            raise RuntimeError(
                "CANARY_ALT_PREFIX_NOT_UNIQUE:"
                +str(preferred_prefix)
            )
        else:
            print(
                "[CANARY_ALT_PREFIX_STALE] "
                "prefix=%s fallback=current_ready"
                %preferred_prefix,
                flush=True,
            )

    locally_saved=_local_saved_tokens(root)

    unsaved=[
        p for p in pairs
        if str(p.token) not in locally_saved
    ]

    if unsaved:
        pairs=unsaved

    if not pairs:
        raise RuntimeError(
            "CANARY_ALT_NO_SELECTABLE_READY_PAIR"
        )

    pair=sorted(
        pairs,
        key=lambda p:str(p.token),
    )[0]

    print(
        "[CANARY_ALT_SELECTED] "
        "token=%s pump=%s ready_pairs=%d local_saved=%s"
        %(
            str(pair.token)[:12],
            str(pair.pump_pool)[:12],
            len(ready),
            str(pair.token) in locally_saved,
        ),
        flush=True,
    )

    return pair


def _cached_full_route(token):
    token=str(token)

    pump=rt.TEMPLATES.get(token)
    meteora=rt.METEORA_TEMPLATES.get(token)

    if not isinstance(pump,dict):
        raise RuntimeError(
            "CANARY_ALT_PUMP_TEMPLATE_MISSING:"
            +token
        )

    if not isinstance(meteora,dict):
        raise RuntimeError(
            "CANARY_ALT_METEORA_TEMPLATE_MISSING:"
            +token
        )

    p_ixs=[
        dict(ix)
        for ix in list(
            pump.get("instructions")
            or []
        )
    ]

    if not p_ixs:
        raise RuntimeError(
            "CANARY_ALT_EMPTY_PUMP_TEMPLATE"
        )

    accounts=[]

    for pubkey,signer,writable in list(
        meteora.get("fixed_accounts")
        or []
    ):
        accounts.append({
            "pubkey":str(pubkey),
            "isSigner":bool(signer),
            "isWritable":bool(writable),
        })

    for _,address in list(
        meteora.get("arrays")
        or []
    ):
        accounts.append({
            "pubkey":str(address),
            "isSigner":False,
            "isWritable":True,
        })

    if len(accounts)<16:
        raise RuntimeError(
            "CANARY_ALT_METEORA_ACCOUNTS_TOO_SMALL:"
            +str(len(accounts))
        )

    meteora_ix={
        "programId":rt.q87.c.DLMM,
        "accounts":accounts,
        "data":"",
    }

    candidates=(
        rt.q87.las.q59
        .candidate_instruction_sets(
            p_ixs,
            meteora_ix,
        )
    )

    live=[]

    for name,ixs in candidates:
        if "PUMP_METEORA_ONLY" in str(name):
            continue
        live.append({
            "name":str(name),
            "instructions":list(ixs),
            "pump_optional_removed":0,
        })

    if not live:
        raise RuntimeError(
            "CANARY_ALT_NO_HELPER_PRESERVING_CANDIDATE"
        )

    return {
        "token":token,
        "base_alts":[],
        "live_candidates":live,
    }


def _cached_alt_addresses(token,user):
    route=_cached_full_route(token)

    addresses=q96._alt_addresses_from_route(
        route,
        user,
    )

    if len(addresses)<4:
        raise RuntimeError(
            "CANARY_ALT_TOO_FEW_CACHED_ADDRESSES"
        )

    print(
        "[CANARY_ALT_CACHED_ADDRESSES] "
        "token=%s count=%d "
        "getProgramAccounts=FALSE"
        %(
            str(token)[:10],
            len(addresses),
        ),
        flush=True,
    )

    return addresses


def _persist_state(
    root,
    token,
    setup,
    signature,
    before,
    after,
):
    state=q96._load_alt_state(root)
    tables=state.get("tables")

    if not isinstance(tables,dict):
        tables={}
        state["tables"]=tables

    tables[str(token)]={
        "address":setup["lookupTable"],
        "addresses":setup["addresses"],
        "recent_slot":setup["recentSlot"],
        "signature":signature,
        "wallet_delta_lamports":
            int(after)-int(before),
        "created_unix":time.time(),
    }

    q96._atomic(
        q96._qarb096_alt_state_path(root),
        state,
    )


def _wait_active(
    alt,
    setup_slot,
    deadline,
):
    while time.monotonic()<deadline:
        try:
            slot=int(
                _retry_rpc(
                    "getSlot",
                    [{
                        "commitment":"confirmed"
                    }],
                )
            )

            got=_retry_rpc(
                "getAccountInfo",
                [
                    alt,
                    {
                        "encoding":"base64",
                        "commitment":"confirmed",
                    },
                ],
            )

            value=(
                got.get("value")
                if isinstance(got,dict)
                else None
            )

            if (
                slot>int(setup_slot)
                and isinstance(value,dict)
                and value.get("data")
            ):
                return True

        except Exception:
            pass

        time.sleep(0.4)

    return False


def bootstrap_one(
    root=None,
    preferred_prefix=None,
    activation_seconds=30.0,
):
    root=Path(root or Path.cwd())

    state,_=rt.q25.prepare_once(root)
    rt.q25.bind_cached_state(state)

    kp,user=rt.q87.c.sim_identity()

    if kp is None:
        raise RuntimeError(
            "QSB_SOLANA_PRIVATE_KEY_MISSING"
        )

    ready=_initialize_ready(state,user)

    print(
        "[CANARY_ALT_READY_SET] "
        "count=%d tokens=%s"
        %(
            len(ready),
            ",".join(
                x[:10]
                for x in sorted(ready)
            ),
        ),
        flush=True,
    )

    pair=_select_current_pair(
        root,
        state,
        preferred_prefix,
    )

    token=str(pair.token)

    existing=_call_with_retry_rpc(
        q96._saved_alt,
        root,
        token,
    )

    if existing:
        print(
            "[CANARY_ALT_ALREADY_READY] "
            "token=%s address=%s"
            %(token[:10],existing),
            flush=True,
        )
        return {
            "ok":True,
            "created":False,
            "token":token,
            "address":existing,
        }

    addresses=_cached_alt_addresses(
        token,
        user,
    )

    setup=_call_with_retry_rpc(
        q96._build_alt_setup,
        user,
        addresses,
    )

    bh=_retry_rpc(
        "getLatestBlockhash",
        [{
            "commitment":"confirmed"
        }],
    )["value"]["blockhash"]

    msg,unsigned=rt.q87.c.compile_v0(
        user,
        setup["instructions"],
        [],
        bh,
    )

    raw=rt.q87.c.signed_tx(msg,kp)

    if len(raw)>MAX_TX_BYTES:
        raise RuntimeError(
            "CANARY_ALT_SETUP_TOO_LARGE:"
            +str(len(raw))
        )

    sim=_call_with_retry_rpc(
        q96.signed_simulation,
        raw,
    )

    if sim.get("err") is not None:
        raise RuntimeError(
            "CANARY_ALT_SETUP_SIM_ERROR:"
            +str(sim.get("err"))
        )

    before=int(
        _retry_rpc(
            "getBalance",
            [
                str(user),
                {
                    "commitment":"confirmed"
                },
            ],
        )["value"]
    )

    print(
        "[CANARY_ALT_SETUP] "
        "token=%s addresses=%d "
        "setup_bytes=%d simulation=PASS "
        "trade_broadcast=FALSE"
        %(
            token[:10],
            len(setup["addresses"]),
            len(raw),
        ),
        flush=True,
    )

    signature=q96.send_once(raw)

    deadline=(
        time.monotonic()
        +max(
            10.0,
            float(activation_seconds),
        )
    )

    tx=_call_with_retry_rpc(
        q96.wait_confirmed,
        signature,
        deadline,
    )

    if tx is None:
        raise RuntimeError(
            "CANARY_ALT_CONFIRMATION_UNKNOWN:"
            +str(signature)
        )

    err=(
        tx.get("meta",{})
        or {}
    ).get("err")

    if err is not None:
        raise RuntimeError(
            "CANARY_ALT_CONFIRMED_ERROR:"
            +str(err)
        )

    after=int(
        _retry_rpc(
            "getBalance",
            [
                str(user),
                {
                    "commitment":"confirmed"
                },
            ],
        )["value"]
    )

    _persist_state(
        root,
        token,
        setup,
        signature,
        before,
        after,
    )

    alt=str(setup["lookupTable"])

    active=_wait_active(
        alt,
        int(tx.get("slot",0) or 0),
        deadline,
    )

    print(
        "[CANARY_ALT_CONFIRMED] "
        "token=%s address=%s "
        "signature=%s "
        "wallet_delta_lamports=%d "
        "active=%s"
        %(
            token[:10],
            alt,
            signature,
            after-before,
            active,
        ),
        flush=True,
    )

    return {
        "ok":True,
        "created":True,
        "token":token,
        "address":alt,
        "signature":signature,
        "wallet_delta_lamports":
            after-before,
        "active":active,
    }


def main():
    p=argparse.ArgumentParser()

    p.add_argument(
        "--preferred-prefix",
        default=None,
    )

    p.add_argument(
        "--activation-seconds",
        type=float,
        default=30.0,
    )

    a=p.parse_args()

    result=bootstrap_one(
        preferred_prefix=
            a.preferred_prefix,
        activation_seconds=
            a.activation_seconds,
    )

    if not result.get("ok"):
        return 1

    print(
        "[NEXT] python -m "
        "qseries_v2.oracle_execution."
        "solana_atomic_executor.runtime "
        "--seconds 300",
        flush=True,
    )

    return 0


if __name__=="__main__":
    raise SystemExit(main())
