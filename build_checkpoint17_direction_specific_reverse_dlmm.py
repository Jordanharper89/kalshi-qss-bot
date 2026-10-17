from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint17_pair_key_execution_templates.py"
TEST=ROOT/"test_canonical_checkpoint17_pair_key_execution_templates.py"
EXTRA_TEST=ROOT/"test_checkpoint17_direction_specific_dlmm_templates.py"

MODULE=r"""from __future__ import annotations

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

    key=_direction_key(
        token,
        pool,
        direction,
    )

    template=PAIR_TEMPLATES.get(key)

    if template is None:
        raise RuntimeError(
            "PAIR_KEY_DIRECTION_TEMPLATE_MISSING:"
            +key
        )

    quote=dict(
        opportunity.get("mq")
        or {}
    )

    if "swap_for_y" not in quote:
        raise RuntimeError(
            "CHECKPOINT17_QUOTE_DIRECTION_MISSING:"
            +key
        )

    if bool(
        quote["swap_for_y"]
    )!=bool(
        template["swap_for_y"]
    ):
        raise RuntimeError(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH:"
            +key
            +":quote="
            +str(bool(quote["swap_for_y"]))
            +":template="
            +str(bool(template["swap_for_y"]))
        )

    accounts=list(
        template["fixed_accounts"]
    )

    if len(accounts)<6:
        raise RuntimeError(
            "CHECKPOINT17_DIRECTION_TEMPLATE_ACCOUNTS_SHORT:"
            +key
        )

    if str(accounts[4][0])!=str(
        template["source"]
    ):
        raise RuntimeError(
            "CHECKPOINT17_SOURCE_ACCOUNT_DRIFT:"
            +key
        )

    if str(accounts[5][0])!=str(
        template["dest"]
    ):
        raise RuntimeError(
            "CHECKPOINT17_DEST_ACCOUNT_DRIFT:"
            +key
        )

    with ROUTE_LOCK:
        old=dict(r.METEORA_TEMPLATES)

        try:
            r.METEORA_TEMPLATES={
                token:copy.deepcopy(
                    template
                )
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
                    +key
                )

            if str(
                active.get("direction")
            )!=direction:
                raise RuntimeError(
                    "CHECKPOINT17_ROUTE_DIRECTION_DRIFT:"
                    +key
                )

            if bool(
                active.get("swap_for_y")
            )!=bool(
                quote["swap_for_y"]
            ):
                raise RuntimeError(
                    "CHECKPOINT17_ACTIVE_DIRECTION_DRIFT:"
                    +key
                )

            print(
                "[CHECKPOINT17_ROUTE_DIRECTION] "
                "pair=%s dir=%s source=%s dest=%s "
                "swap_for_y=%s"
                %(
                    _pair_key(
                        token,
                        pool,
                    )[:28],
                    direction,
                    str(
                        active["source"]
                    )[:12],
                    str(
                        active["dest"]
                    )[:12],
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
    ORIGINAL_ROUTE=old_route

    try:
        c12._expanded_state=lambda:(
            state,
            registry,
            failures,
        )

        c7._route=_pair_bound_route
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
        c12._expanded_state=old_expanded
        c7._route=old_route


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint17_pair_key_execution_templates.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(
            encoding="utf-8"
        )
        ast.parse(cls.s)

    def test_pair_key_identity(self):
        self.assertIn(
            'str(token)+"|"+str(pool)',
            self.s,
        )
        self.assertIn(
            '+"|"+direction',
            self.s,
        )

    def test_single_batched_bitmap_rpc(self):
        self.assertIn(
            "CHECKPOINT17_BITMAP_BATCH",
            self.s,
        )
        self.assertIn(
            '"getMultipleAccounts"',
            self.s,
        )
        self.assertNotIn(
            'r.prebuild_meteora_templates({"pairs":[pair]}',
            self.s,
        )

    def test_transport_failures_retry(self):
        self.assertIn(
            "urllib.error.URLError",
            self.s,
        )
        self.assertIn(
            "TimeoutError",
            self.s,
        )
        self.assertIn(
            "CHECKPOINT17_BITMAP_RETRY",
            self.s,
        )

    def test_all_direction_templates_preserved(self):
        self.assertIn(
            "expected_templates=expected_pairs*2",
            self.s,
        )
        self.assertIn(
            "CHECKPOINT17_DIRECTION_TEMPLATE_COVERAGE",
            self.s,
        )

    def test_pool_drift_fails_closed(self):
        self.assertIn(
            "CHECKPOINT17_ROUTE_POOL_DRIFT",
            self.s,
        )

    def test_route_is_pair_direction_bound(self):
        self.assertIn(
            "c7._route=_pair_bound_route",
            self.s,
        )
        self.assertIn(
            "PAIR_KEY_DIRECTION_TEMPLATE_MISSING",
            self.s,
        )
        self.assertIn(
            "CHECKPOINT17_ROUTE_DIRECTION_DRIFT",
            self.s,
        )

    def test_forward_semantics(self):
        self.assertIn(
            'if direction==FORWARD:',
            self.s,
        )
        self.assertIn(
            '"PUMP_TO_METEORA"',
            self.s,
        )
        self.assertIn(
            '"METEORA_TO_PUMP"',
            self.s,
        )

    def test_reverse_semantics(self):
        self.assertIn(
            '"dest":token_ata',
            self.s,
        )
        self.assertIn(
            '"source":wsol_ata',
            self.s,
        )
        self.assertIn(
            "cp26_account5_create_idempotent_target=True",
            self.s,
        )

    def test_quote_direction_must_match_template(self):
        self.assertIn(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH",
            self.s,
        )

    def test_reuses_checkpoint15(self):
        self.assertIn(
            "return c15.main()",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
"""

EXTRA_TEST_CODE=r"""import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    checkpoint17_pair_key_execution_templates as c17
)


class FakeC:
    WSOL="WSOL"


class FakeQ87:
    c=FakeC()


class FakeR:
    q87=FakeQ87()


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=c17.r
        c17.r=FakeR()

    @classmethod
    def tearDownClass(cls):
        c17.r=cls.old

    def test_token_x_wsol_forward(self):
        x=c17._direction_semantics(
            "WSOL","TOKEN",
            "ATA_WSOL","ATA_TOKEN",
            c17.FORWARD,
        )
        self.assertEqual(x["source"],"ATA_TOKEN")
        self.assertEqual(x["dest"],"ATA_WSOL")
        self.assertFalse(x["swap_for_y"])

    def test_token_x_wsol_reverse(self):
        x=c17._direction_semantics(
            "WSOL","TOKEN",
            "ATA_WSOL","ATA_TOKEN",
            c17.REVERSE,
        )
        self.assertEqual(x["source"],"ATA_WSOL")
        self.assertEqual(x["dest"],"ATA_TOKEN")
        self.assertTrue(x["swap_for_y"])

    def test_token_y_wsol_forward(self):
        x=c17._direction_semantics(
            "TOKEN","WSOL",
            "ATA_TOKEN","ATA_WSOL",
            c17.FORWARD,
        )
        self.assertEqual(x["source"],"ATA_TOKEN")
        self.assertEqual(x["dest"],"ATA_WSOL")
        self.assertTrue(x["swap_for_y"])

    def test_token_y_wsol_reverse(self):
        x=c17._direction_semantics(
            "TOKEN","WSOL",
            "ATA_TOKEN","ATA_WSOL",
            c17.REVERSE,
        )
        self.assertEqual(x["source"],"ATA_WSOL")
        self.assertEqual(x["dest"],"ATA_TOKEN")
        self.assertFalse(x["swap_for_y"])


if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(
    MODULE,
    encoding="utf-8",
)

TEST.write_text(
    TEST_CODE,
    encoding="utf-8",
)

EXTRA_TEST.write_text(
    EXTRA_TEST_CODE,
    encoding="utf-8",
)

for path in (
    TARGET,
    TEST,
    EXTRA_TEST,
):
    ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

print("[PASS] checkpoint-17 direction-specific DLMM template replacement installed")
print("[ROOT_CAUSE] prior template encoded token->WSOL and was reused for reverse")
print("[FORWARD] PUMP_TO_METEORA uses token->WSOL")
print("[REVERSE] METEORA_TO_PUMP uses WSOL->token")
print("[IDENTITY] token|meteora_pool|direction")
print("[ATA] reverse DLMM account[5] is exact user token ATA for CP26 CreateIdempotent")
print("[QUOTE] swap_for_y must match selected direction template")
print("[STARTUP] one batched bitmap RPC preserved")
print("[PIPELINE] real fee + signed simulation preserved")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
print("[TEST]",EXTRA_TEST.name)
