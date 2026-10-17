from __future__ import annotations

import argparse
import copy
import threading
import time
import urllib.error

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint12_multi_pool_live_size_optimizer as c12
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint15_cheapest_legal_fee_signed_simulation as c15

PAIR_TEMPLATES={}
ROUTE_LOCK=threading.Lock()
ORIGINAL_ROUTE=None

FORWARD="PUMP_TO_METEORA"
REVERSE="METEORA_TO_PUMP"


def _pair_key(token,pool):
    return str(token)+"|"+str(pool)


def _direction_key(token,pool,direction):
    direction=str(direction)

    if direction not in (FORWARD,REVERSE):
        raise RuntimeError(
            "CHECKPOINT17_DIRECTION_UNSUPPORTED:"+direction
        )

    return _pair_key(token,pool)+"|"+direction


def _bitmap_batch(addresses):
    last=None

    for attempt in range(1,7):
        try:
            result=r.q87.c.rpc(
                "getMultipleAccounts",
                [
                    list(addresses),
                    {
                        "encoding":"base64",
                        "commitment":"processed",
                    },
                ],
            )

            if not isinstance(result,dict):
                raise RuntimeError(
                    "CHECKPOINT17_BITMAP_RESULT_NOT_MAPPING"
                )

            values=result.get("value")

            if not isinstance(values,list):
                raise RuntimeError(
                    "CHECKPOINT17_BITMAP_VALUE_NOT_LIST"
                )

            if len(values)!=len(addresses):
                raise RuntimeError(
                    "CHECKPOINT17_BITMAP_LENGTH_MISMATCH:"
                    +str(len(values))
                    +"/"
                    +str(len(addresses))
                )

            return values

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
        ) as exc:
            last=exc

            code=getattr(exc,"code",None)
            text=str(exc).lower()

            retryable=(
                code==429
                or "429" in text
                or "timed out" in text
                or "timeout" in text
                or "temporarily unavailable" in text
                or "connection reset" in text
            )

            if not retryable:
                raise

            delay=min(
                8.0,
                0.75*(2**(attempt-1)),
            )

            print(
                "[CHECKPOINT17_BITMAP_RETRY] "
                "attempt=%d sleep=%.2fs reason=%s:%s"
                %(
                    attempt,
                    delay,
                    type(exc).__name__,
                    str(exc)[:160],
                ),
                flush=True,
            )

            time.sleep(delay)

    raise RuntimeError(
        "CHECKPOINT17_BITMAP_BATCH_UNAVAILABLE:"
        +str(last)
    )


def _direction_semantics(
    token_x,
    token_y,
    ux,
    uy,
    direction,
):
    # Meteora DLMM:
    # swap_for_y=True  => X -> Y
    # swap_for_y=False => Y -> X
    #
    # PUMP_TO_METEORA:
    # PumpSwap produces token, Meteora consumes token and produces WSOL.
    #
    # METEORA_TO_PUMP:
    # Meteora consumes WSOL and produces token, PumpSwap consumes token.

    if token_x==r.q87.c.WSOL:
        token_ata=uy
        wsol_ata=ux

        if direction==FORWARD:
            return {
                "source":token_ata,
                "dest":wsol_ata,
                "swap_for_y":False,
                "input_mint":token_y,
                "output_mint":token_x,
                "output_program_side":"X",
            }

        if direction==REVERSE:
            return {
                "source":wsol_ata,
                "dest":token_ata,
                "swap_for_y":True,
                "input_mint":token_x,
                "output_mint":token_y,
                "output_program_side":"Y",
            }

    elif token_y==r.q87.c.WSOL:
        token_ata=ux
        wsol_ata=uy

        if direction==FORWARD:
            return {
                "source":token_ata,
                "dest":wsol_ata,
                "swap_for_y":True,
                "input_mint":token_x,
                "output_mint":token_y,
                "output_program_side":"Y",
            }

        if direction==REVERSE:
            return {
                "source":wsol_ata,
                "dest":token_ata,
                "swap_for_y":False,
                "input_mint":token_y,
                "output_mint":token_x,
                "output_program_side":"X",
            }

    else:
        raise RuntimeError(
            "CHECKPOINT17_DLMM_PAIR_NOT_WSOL:"
            +str(token_x)
            +"|"
            +str(token_y)
        )

    raise RuntimeError(
        "CHECKPOINT17_DIRECTION_SEMANTICS_UNREACHABLE:"
        +str(direction)
    )


def _build_pair_templates(state,user,warmed):
    global PAIR_TEMPLATES

    PAIR_TEMPLATES={}

    programs={
        str(row["token"]):str(row["program"])
        for row in (warmed or [])
        if row.get("token") and row.get("program")
    }

    programs[r.q87.c.WSOL]=r.q87.c.TOKEN

    ready=set(r.READY_TOKENS)
    descriptors=[]

    for pair in list(state.get("pairs") or []):
        token=str(pair.token)
        pool=str(pair.meteora_pool)
        pair_key=_pair_key(token,pool)

        if token not in ready:
            raise RuntimeError(
                "CHECKPOINT17_PUMP_TEMPLATE_NOT_READY:"
                +pair_key
            )

        token_x=str(pair.token_x)
        token_y=str(pair.token_y)

        tx_prog=programs.get(token_x)
        ty_prog=programs.get(token_y)

        if not tx_prog or not ty_prog:
            raise RuntimeError(
                "CHECKPOINT17_TOKEN_PROGRAM_NOT_PREWARMED:"
                +pair_key
            )

        ux=r.q87.c.ata(
            user,
            token_x,
            tx_prog,
        )

        uy=r.q87.c.ata(
            user,
            token_y,
            ty_prog,
        )

        rx=r.q87.c.pda(
            [
                r.q87.c.b58d(pool),
                r.q87.c.b58d(token_x),
            ],
            r.q87.c.DLMM,
        )

        ry=r.q87.c.pda(
            [
                r.q87.c.b58d(pool),
                r.q87.c.b58d(token_y),
            ],
            r.q87.c.DLMM,
        )

        oracle=r.q87.c.pda(
            [
                b"oracle",
                r.q87.c.b58d(pool),
            ],
            r.q87.c.DLMM,
        )

        bitmap=r.q87.c.pda(
            [
                b"bitmap",
                r.q87.c.b58d(pool),
            ],
            r.q87.c.DLMM,
        )

        event_authority=r.q87.c.pda(
            [b"__event_authority"],
            r.q87.c.DLMM,
        )

        arrays=[
            (int(a[0]),str(a[1]))
            for a in list(pair.arrays)
        ]

        arrays.sort(
            key=lambda x:x[0]
        )

        if not arrays:
            raise RuntimeError(
                "CHECKPOINT17_NO_PREWARMED_DLMM_ARRAYS:"
                +pair_key
            )

        descriptors.append({
            "pair_key":pair_key,
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
            "event_authority":event_authority,
            "arrays":arrays,
        })

    if not descriptors:
        raise RuntimeError(
            "CHECKPOINT17_NO_PAIR_DESCRIPTORS"
        )

    bitmap_values=_bitmap_batch(
        [
            row["bitmap"]
            for row in descriptors
        ]
    )

    for row,bitmap_account in zip(
        descriptors,
        bitmap_values,
    ):
        bitmap_key=(
            row["bitmap"]
            if bitmap_account
            else r.q87.c.DLMM
        )

        for direction in (
            FORWARD,
            REVERSE,
        ):
            semantics=_direction_semantics(
                row["token_x"],
                row["token_y"],
                row["ux"],
                row["uy"],
                direction,
            )

            fixed_accounts=[
                (row["pool"],False,True),
                (bitmap_key,False,True),
                (row["rx"],False,True),
                (row["ry"],False,True),
                (semantics["source"],False,True),
                (semantics["dest"],False,True),
                (row["token_x"],False,False),
                (row["token_y"],False,False),
                (row["oracle"],False,True),
                (r.q87.c.DLMM,False,True),
                (user,True,False),
                (row["tx_prog"],False,False),
                (row["ty_prog"],False,False),
                (row["event_authority"],False,False),
                (r.q87.c.DLMM,False,False),
            ]

            template={
                "pool":row["pool"],
                "token":row["token"],
                "token_x":row["token_x"],
                "token_y":row["token_y"],
                "tx_prog":row["tx_prog"],
                "ty_prog":row["ty_prog"],
                "ux":row["ux"],
                "uy":row["uy"],
                "direction":direction,
                "source":semantics["source"],
                "dest":semantics["dest"],
                "input_mint":semantics["input_mint"],
                "output_mint":semantics["output_mint"],
                "output_program_side":semantics["output_program_side"],
                "swap_for_y":bool(
                    semantics["swap_for_y"]
                ),
                "arrays":list(row["arrays"]),
                "fixed_accounts":fixed_accounts,
            }

            direction_key=_direction_key(
                row["token"],
                row["pool"],
                direction,
            )

            PAIR_TEMPLATES[
                direction_key
            ]=template

            print(
                "[CHECKPOINT17_DIRECTION_TEMPLATE_READY] "
                "pair=%s dir=%s source=%s dest=%s "
                "swap_for_y=%s arrays=%d bitmap=%s"
                %(
                    row["pair_key"][:28],
                    direction,
                    semantics["source"][:12],
                    semantics["dest"][:12],
                    str(
                        bool(
                            semantics[
                                "swap_for_y"
                            ]
                        )
                    ),
                    len(row["arrays"]),
                    (
                        "EXTENSION"
                        if bitmap_account
                        else "PROGRAM_SENTINEL"
                    ),
                ),
                flush=True,
            )

    expected_pairs=len(
        list(state.get("pairs") or [])
    )

    expected_templates=expected_pairs*2

    if len(PAIR_TEMPLATES)!=expected_templates:
        raise RuntimeError(
            "CHECKPOINT17_DIRECTION_TEMPLATE_COVERAGE:%d/%d"
            %(
                len(PAIR_TEMPLATES),
                expected_templates,
            )
        )

    print(
        "[CHECKPOINT17_BITMAP_BATCH] "
        "pairs=%d templates=%d rpc_calls=1"
        %(
            expected_pairs,
            len(PAIR_TEMPLATES),
        ),
        flush=True,
    )

    return len(PAIR_TEMPLATES)


def _pair_bound_route(
    user,
    snap,
    opportunity,
):
    token=str(snap["token"])
    pool=str(snap["meteora"]["address"])
    direction=str(
        opportunity.get("direction")
        or ""
    )

    exact_key=_direction_key(
        token,
        pool,
        direction,
    )

    exact_template=PAIR_TEMPLATES.get(
        exact_key
    )

    if exact_template is None:
        raise RuntimeError(
            "PAIR_KEY_DIRECTION_TEMPLATE_MISSING:"
            +exact_key
        )

    quote=dict(
        opportunity.get("mq")
        or {}
    )

    if "swap_for_y" not in quote:
        raise RuntimeError(
            "CHECKPOINT17_QUOTE_DIRECTION_MISSING:"
            +exact_key
        )

    exact_swap=bool(
        exact_template["swap_for_y"]
    )

    quote_swap=bool(
        quote["swap_for_y"]
    )

    if quote_swap!=exact_swap:
        raise RuntimeError(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH:"
            +exact_key
            +":quote="
            +str(quote_swap)
            +":exact="
            +str(exact_swap)
        )

    # checkpoint-7 legacy reverse route still performs one inversion
    # internally. Reverse therefore receives the certified forward
    # template as the legacy seed exactly once. The live quote and the
    # exact reverse template remain the source of truth.
    if direction==REVERSE:
        seed_key=_direction_key(
            token,
            pool,
            FORWARD,
        )

        seed_template=PAIR_TEMPLATES.get(
            seed_key
        )

        if seed_template is None:
            raise RuntimeError(
                "CHECKPOINT17_LEGACY_REVERSE_SEED_MISSING:"
                +seed_key
            )

        seed_swap=bool(
            seed_template["swap_for_y"]
        )

        if seed_swap==exact_swap:
            raise RuntimeError(
                "CHECKPOINT17_REVERSE_SEED_NOT_OPPOSITE:"
                +exact_key
            )

        seed_accounts=list(
            seed_template.get(
                "fixed_accounts"
            )
            or []
        )

        exact_accounts=list(
            exact_template.get(
                "fixed_accounts"
            )
            or []
        )

        if (
            len(seed_accounts)<6
            or len(exact_accounts)<6
        ):
            raise RuntimeError(
                "CHECKPOINT17_DIRECTION_TEMPLATE_ACCOUNTS_SHORT:"
                +exact_key
            )

        if (
            str(seed_accounts[5][0])
            !=str(exact_accounts[4][0])
            or
            str(seed_accounts[4][0])
            !=str(exact_accounts[5][0])
        ):
            raise RuntimeError(
                "CHECKPOINT17_REVERSE_SEED_ACCOUNT_INVARIANT:"
                +exact_key
            )

        active_template=copy.deepcopy(
            seed_template
        )

        print(
            "[CHECKPOINT17_LEGACY_REVERSE_SEED] "
            "pair=%s seed_dir=%s seed_swap=%s "
            "physical_dir=%s physical_swap=%s "
            "quote_swap=%s invariant=PASS"
            %(
                _pair_key(
                    token,
                    pool,
                )[:28],
                FORWARD,
                str(seed_swap),
                REVERSE,
                str(exact_swap),
                str(quote_swap),
            ),
            flush=True,
        )

    elif direction==FORWARD:
        active_template=copy.deepcopy(
            exact_template
        )

    else:
        raise RuntimeError(
            "CHECKPOINT17_DIRECTION_UNSUPPORTED:"
            +direction
        )

    with ROUTE_LOCK:
        old=dict(r.METEORA_TEMPLATES)

        try:
            r.METEORA_TEMPLATES={
                token:active_template
            }

            active=(
                r.METEORA_TEMPLATES[
                    token
                ]
            )

            if str(
                active.get("pool")
            )!=pool:
                raise RuntimeError(
                    "CHECKPOINT17_ROUTE_POOL_DRIFT:"
                    +exact_key
                )

            print(
                "[CHECKPOINT17_ROUTE_DIRECTION] "
                "pair=%s dir=%s "
                "physical_source=%s physical_dest=%s "
                "physical_swap_for_y=%s "
                "legacy_seed_swap_for_y=%s"
                %(
                    _pair_key(
                        token,
                        pool,
                    )[:28],
                    direction,
                    str(
                        exact_template[
                            "source"
                        ]
                    )[:12],
                    str(
                        exact_template[
                            "dest"
                        ]
                    )[:12],
                    str(exact_swap),
                    str(
                        bool(
                            active[
                                "swap_for_y"
                            ]
                        )
                    ),
                ),
                flush=True,
            )

            return ORIGINAL_ROUTE(
                user,
                snap,
                opportunity,
            )

        finally:
            r.METEORA_TEMPLATES=old



def main():
    global ORIGINAL_ROUTE

    p=argparse.ArgumentParser()

    p.add_argument(
        "--seconds",
        type=float,
        default=3600.0,
    )

    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError(
            "CHECKPOINT17_SECONDS_MUST_BE_POSITIVE"
        )

    state,registry,failures=(
        c12._expanded_state()
    )

    warmed=(
        r.q25
        .install_hot_math_and_prewarm(
            state
        )
    )

    r.q18.install_exact_hot_math()

    signer,user=r.q87.c.sim_identity()

    if signer is None or not user:
        raise RuntimeError(
            "CHECKPOINT17_SIGNER_UNAVAILABLE"
        )

    r.prebuild_templates(
        state,
        user,
    )

    template_count=(
        _build_pair_templates(
            state,
            user,
            warmed,
        )
    )

    old_expanded=c12._expanded_state
    old_route=c7._route
    old_prewarm=r.q25.install_hot_math_and_prewarm
    ORIGINAL_ROUTE=old_route

    try:
        c12._expanded_state=lambda:(
            state,
            registry,
            failures,
        )

        c7._route=_pair_bound_route

        def _reuse_checkpoint17_prewarm(child_state):
            child_pairs=list(
                child_state.get("pairs") or []
            )
            parent_pairs=list(
                state.get("pairs") or []
            )

            child_tokens={
                str(pair.token)
                for pair in child_pairs
            }
            parent_tokens={
                str(pair.token)
                for pair in parent_pairs
            }

            if child_tokens!=parent_tokens:
                raise RuntimeError(
                    "CHECKPOINT17_PREWARM_STATE_DRIFT:"
                    +str(len(child_tokens))
                    +"/"
                    +str(len(parent_tokens))
                )

            print(
                "[CHECKPOINT17_SINGLE_PREWARM_HANDOFF] "
                "tokens=%d warmed_rows=%d "
                "duplicate_network_prewarm=False"
                %(
                    len(parent_tokens),
                    len(warmed),
                ),
                flush=True,
            )

            return list(warmed)

        r.q25.install_hot_math_and_prewarm=(
            _reuse_checkpoint17_prewarm
        )

        c15.SECONDS=float(args.seconds)

        print(
            "[CHECKPOINT17_ACTIVATION] "
            "direction_specific_pair_templates=True "
            "batched_bitmap_startup=True "
            "seconds=%.0f broadcast=False"
            %c15.SECONDS,
            flush=True,
        )

        print(
            "[CHECKPOINT17_COVERAGE] "
            "live_pairs=%d templates=%d "
            "identity=token|meteora_pool|direction"
            %(
                len(state["pairs"]),
                template_count,
            ),
            flush=True,
        )

        print(
            "[CHECKPOINT17_DIRECTION_POLICY] "
            "PUMP_TO_METEORA=token_to_wsol "
            "METEORA_TO_PUMP=wsol_to_token",
            flush=True,
        )

        print(
            "[CHECKPOINT17_REVERSE_OUTPUT] "
            "METEORA_TO_PUMP dest=exact_user_token_ata "
            "cp26_account5_create_idempotent_target=True",
            flush=True,
        )

        print(
            "[CHECKPOINT17_STARTUP] "
            "bitmap_rpc=single_batch "
            "per_pair_bitmap_rpc=False",
            flush=True,
        )

        print(
            "[CHECKPOINT17_PIPELINE] "
            "gross_positive -> exact_pair_direction_route -> "
            "all_legal_candidates -> real_fee_each -> "
            "best_after_fee -> signed_simulation",
            flush=True,
        )

        print(
            "[BROADCAST] disabled",
            flush=True,
        )

        return c15.main()

    finally:
        r.q25.install_hot_math_and_prewarm=old_prewarm
        c12._expanded_state=old_expanded
        c7._route=old_route


if __name__=="__main__":
    raise SystemExit(main())
