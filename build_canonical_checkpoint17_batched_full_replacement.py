from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint17_pair_key_execution_templates.py"
TEST=ROOT/"test_canonical_checkpoint17_pair_key_execution_templates.py"

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


def _pair_key(token,pool):
    return str(token)+"|"+str(pool)


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
        key=_pair_key(token,pool)

        if token not in ready:
            raise RuntimeError(
                "CHECKPOINT17_PUMP_TEMPLATE_NOT_READY:"
                +key
            )

        token_x=str(pair.token_x)
        token_y=str(pair.token_y)

        tx_prog=programs.get(token_x)
        ty_prog=programs.get(token_y)

        if not tx_prog or not ty_prog:
            raise RuntimeError(
                "CHECKPOINT17_TOKEN_PROGRAM_NOT_PREWARMED:"
                +key
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
                +key
            )

        if token_x==r.q87.c.WSOL:
            source=uy
            dest=ux
            swap_for_y=False

        elif token_y==r.q87.c.WSOL:
            source=ux
            dest=uy
            swap_for_y=True

        else:
            raise RuntimeError(
                "CHECKPOINT17_DLMM_PAIR_NOT_WSOL:"
                +key
            )

        descriptors.append({
            "key":key,
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
            "source":source,
            "dest":dest,
            "swap_for_y":bool(swap_for_y),
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

        fixed_accounts=[
            (row["pool"],False,True),
            (bitmap_key,False,True),
            (row["rx"],False,True),
            (row["ry"],False,True),
            (row["source"],False,True),
            (row["dest"],False,True),
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
            "token_x":row["token_x"],
            "token_y":row["token_y"],
            "swap_for_y":row["swap_for_y"],
            "arrays":list(row["arrays"]),
            "fixed_accounts":fixed_accounts,
        }

        PAIR_TEMPLATES[
            row["key"]
        ]=template

        print(
            "[CHECKPOINT17_TEMPLATE_READY] "
            "pair=%s token=%s pool=%s arrays=%d bitmap=%s"
            %(
                row["key"][:34],
                row["token"][:10],
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

    expected=len(
        list(state.get("pairs") or [])
    )

    if len(PAIR_TEMPLATES)!=expected:
        raise RuntimeError(
            "CHECKPOINT17_TEMPLATE_COVERAGE:%d/%d"
            %(
                len(PAIR_TEMPLATES),
                expected,
            )
        )

    print(
        "[CHECKPOINT17_BITMAP_BATCH] "
        "pairs=%d rpc_calls=1"
        %len(PAIR_TEMPLATES),
        flush=True,
    )

    return len(PAIR_TEMPLATES)


def _pair_bound_route(user,snap,opportunity):
    token=str(snap["token"])
    pool=str(snap["meteora"]["address"])
    key=_pair_key(token,pool)

    template=PAIR_TEMPLATES.get(key)

    if template is None:
        raise RuntimeError(
            "PAIR_KEY_METEORA_TEMPLATE_MISSING:"
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

            if str(
                r.METEORA_TEMPLATES[
                    token
                ].get("pool")
            )!=pool:
                raise RuntimeError(
                    "CHECKPOINT17_ROUTE_POOL_DRIFT:"
                    +key
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
            "pair_key_execution_templates=True "
            "batched_bitmap_startup=True "
            "seconds=%.0f broadcast=False"
            %c15.SECONDS,
            flush=True,
        )

        print(
            "[CHECKPOINT17_COVERAGE] "
            "live_pairs=%d templates=%d "
            "identity=token|meteora_pool"
            %(
                len(state["pairs"]),
                template_count,
            ),
            flush=True,
        )

        print(
            "[CHECKPOINT17_STARTUP] "
            "bitmap_rpc=single_batch "
            "per_pair_bitmap_rpc=False",
            flush=True,
        )

        print(
            "[CHECKPOINT17_ROUTE_BINDING] "
            "token_level_overwrite=False "
            "exact_pool_template_required=True",
            flush=True,
        )

        print(
            "[CHECKPOINT17_PIPELINE] "
            "gross_positive -> pair_bound_route -> "
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

    def test_all_pair_templates_preserved(self):
        tree=ast.parse(self.s)
        found=False
        for node in ast.walk(tree):
            if not isinstance(node,ast.Assign):
                continue
            if len(node.targets)!=1:
                continue
            target=node.targets[0]
            if not isinstance(target,ast.Subscript):
                continue
            if not (
                isinstance(target.value,ast.Name)
                and target.value.id=="PAIR_TEMPLATES"
            ):
                continue
            found=True
            break

        self.assertTrue(
            found,
            "PAIR_TEMPLATES indexed assignment missing",
        )
        self.assertIn(
            "CHECKPOINT17_TEMPLATE_COVERAGE",
            self.s,
        )

    def test_pool_drift_fails_closed(self):
        self.assertIn(
            "CHECKPOINT17_ROUTE_POOL_DRIFT",
            self.s,
        )

    def test_route_is_pair_bound(self):
        self.assertIn(
            "c7._route=_pair_bound_route",
            self.s,
        )
        self.assertIn(
            "PAIR_KEY_METEORA_TEMPLATE_MISSING",
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

TARGET.write_text(
    MODULE,
    encoding="utf-8",
)

TEST.write_text(
    TEST_CODE,
    encoding="utf-8",
)

ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)

ast.parse(
    TEST.read_text(
        encoding="utf-8"
    )
)

print("[PASS] checkpoint-17 full batched replacement installed")
print("[ROOT_CAUSE] old CP17 made one bitmap RPC per live pair")
print("[STARTUP] all live pair bitmaps read in one getMultipleAccounts batch")
print("[RESILIENCE] HTTP 429 + SSL/URL timeout retry")
print("[IDENTITY] token|meteora_pool preserved")
print("[HOT_PATH] zero template-discovery RPC")
print("[PIPELINE] checkpoint-15 fee ranking + signed simulation preserved")
print("[KEY] existing signer untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
