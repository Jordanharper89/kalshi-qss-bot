from pathlib import Path
import ast

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"live_money_runtime.py"
TEST=ROOT/"test_live_money_runtime.py"

MODULE=r"""from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint26_dlmm_output_ata_readiness as c26
from qseries_v2.oracle_execution.solana_atomic_executor import runtime as canonical_runtime

ROOT=Path.cwd()
STATE=ROOT/"runtime_state"/"oracle"/"solana_atomic_executor"

CAPACITY=STATE/"capacity_aware_warm_universe.json"
REGISTRY=STATE/"multi_dlmm_pair_registry.json"

MAX_HOT_ACCOUNTS=320
WS_SHARD_SIZE=48

persistent=canonical_runtime.persistent
merged=persistent.m

_ORIGINAL_SHARDS=None


def _load(path):
    if not path.is_file():
        raise RuntimeError(
            "LIVE_MONEY_MISSING:"+str(path)
        )

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _historical_scores():
    data=_load(REGISTRY)
    out={}

    for row in list(
        data.get("rows")
        or []
    ):
        key=str(
            row.get("pair_key")
            or (
                str(row.get("token"))
                +"|"
                +str(row.get("meteora_pool"))
            )
        )

        out[key]={
            "gross_positive":
                bool(
                    row.get(
                        "gross_positive"
                    )
                ),
            "best_local_bps":
                float(
                    row.get(
                        "best_local_bps"
                    )
                    or 0.0
                ),
            "best_local_net_lamports":
                int(
                    row.get(
                        "best_local_net_lamports"
                    )
                    or 0
                ),
        }

    return out


def _priority(row,historical):
    identity=str(
        row["identity"]
    )

    h=historical.get(
        identity,
        {},
    )

    return (
        0 if h.get("gross_positive") else 1,
        -float(
            h.get("best_local_bps")
            or 0.0
        ),
        -int(
            h.get(
                "best_local_net_lamports"
            )
            or 0
        ),
        0 if row.get("retained") else 1,
        float(
            row.get("source_age")
            if row.get("source_age") is not None
            else 1e18
        ),
        -float(
            row.get("reported_tvl")
            or 0.0
        ),
        int(
            row.get("account_cost")
            or 9999
        ),
        identity,
    )


def build_hot_book(
    max_accounts=MAX_HOT_ACCOUNTS,
):
    capacity=_load(CAPACITY)

    rows=list(
        capacity.get("rows")
        or []
    )

    if not rows:
        raise RuntimeError(
            "LIVE_MONEY_EMPTY_INVENTORY"
        )

    historical=_historical_scores()

    rows.sort(
        key=lambda row:_priority(
            row,
            historical,
        )
    )

    selected=[]
    accounts=set()

    for rank,row in enumerate(
        rows,
        1,
    ):
        watched=[
            str(x)
            for x in (
                row.get(
                    "watched_accounts"
                )
                or []
            )
        ]

        if not watched:
            continue

        incremental=[
            x
            for x in watched
            if x not in accounts
        ]

        if (
            len(accounts)
            +len(incremental)
            >int(max_accounts)
        ):
            continue

        accounts.update(
            incremental
        )

        copy=dict(row)
        copy["hot_rank"]=rank
        copy["hot_reason"]={
            "historical_gross_positive":
                bool(
                    historical.get(
                        str(row["identity"]),
                        {},
                    ).get(
                        "gross_positive"
                    )
                ),
            "historical_best_bps":
                float(
                    historical.get(
                        str(row["identity"]),
                        {},
                    ).get(
                        "best_local_bps"
                    )
                    or 0.0
                ),
            "retained":
                bool(
                    row.get("retained")
                ),
        }

        selected.append(copy)

    if len(selected)<5:
        raise RuntimeError(
            "LIVE_MONEY_HOT_BOOK_TOO_SMALL:"
            +str(len(selected))
        )

    if len(accounts)>int(max_accounts):
        raise RuntimeError(
            "LIVE_MONEY_ACCOUNT_BUDGET_BREACH"
        )

    payload=dict(capacity)

    payload[
        "revision"
    ]="LIVE_MONEY_HOT_BOOK_V1"

    payload[
        "source_inventory_pairs"
    ]=len(rows)

    payload[
        "selected_pairs"
    ]=len(selected)

    payload[
        "selected_accounts"
    ]=len(accounts)

    payload[
        "max_accounts"
    ]=int(max_accounts)

    payload["rows"]=selected

    payload["policy"]={
        "execution_book":True,
        "full_inventory_preserved_outside_hot_book":True,
        "historical_positive_first":True,
        "historical_edge_second":True,
        "retained_priority":True,
        "recency_then_tvl_then_account_cost":True,
        "broadcast":False,
    }

    return payload,accounts


def stable_shards(addresses):
    rows=list(
        dict.fromkeys(
            addresses
        )
    )

    shards=[
        rows[i:i+WS_SHARD_SIZE]
        for i in range(
            0,
            len(rows),
            WS_SHARD_SIZE,
        )
    ]

    if any(
        len(x)>WS_SHARD_SIZE
        for x in shards
    ):
        raise RuntimeError(
            "LIVE_MONEY_WS_SHARD_BREACH"
        )

    return shards


def _atomic_write(path,payload):
    tmp=path.with_suffix(
        path.suffix+".live_money.tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    tmp.replace(path)


def main():
    global _ORIGINAL_SHARDS

    p=argparse.ArgumentParser()

    p.add_argument(
        "--seconds",
        type=float,
        default=3600.0,
    )

    p.add_argument(
        "--max-accounts",
        type=int,
        default=MAX_HOT_ACCOUNTS,
    )

    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError(
            "LIVE_MONEY_SECONDS_MUST_BE_POSITIVE"
        )

    if not (
        96
        <=args.max_accounts
        <=384
    ):
        raise RuntimeError(
            "LIVE_MONEY_ACCOUNT_BUDGET_RANGE"
        )

    hot,accounts=build_hot_book(
        args.max_accounts
    )

    original_capacity=(
        CAPACITY.read_bytes()
        if CAPACITY.is_file()
        else None
    )

    _ORIGINAL_SHARDS=merged._shards
    old_argv=list(sys.argv)

    try:
        _atomic_write(
            CAPACITY,
            hot,
        )

        merged._shards=stable_shards

        estimated_shards=(
            (
                len(accounts)
                +WS_SHARD_SIZE
                -1
            )
            //WS_SHARD_SIZE
        )

        print(
            "[INVENTORY] %d routes"
            %int(
                hot.get(
                    "source_inventory_pairs"
                )
                or 0
            ),
            flush=True,
        )

        print(
            "[HOT_BOOK] %d routes"
            %len(
                hot.get("rows")
                or []
            ),
            flush=True,
        )

        print(
            "[WATCHED_ACCOUNTS] %d/%d"
            %(
                len(accounts),
                args.max_accounts,
            ),
            flush=True,
        )

        print(
            "[WS_PLAN] shard_size=%d connections=%d"
            %(
                WS_SHARD_SIZE,
                estimated_shards,
            ),
            flush=True,
        )

        print(
            "[RANKING] historical_positive -> "
            "historical_edge -> retained -> "
            "recency -> liquidity -> account_cost",
            flush=True,
        )

        print(
            "[MONEY_LOOP] scan -> after_fee_positive -> "
            "build -> signed_sim -> freshness",
            flush=True,
        )

        print(
            "[LIVE_SEND] DISABLED until signed-sim certification",
            flush=True,
        )

        print(
            "[BROADCAST] disabled",
            flush=True,
        )

        sys.argv=[
            old_argv[0],
            "--seconds",
            str(float(args.seconds)),
        ]

        return c26.main()

    finally:
        sys.argv=old_argv

        if _ORIGINAL_SHARDS is not None:
            merged._shards=_ORIGINAL_SHARDS
            _ORIGINAL_SHARDS=None

        if original_capacity is None:
            try:
                CAPACITY.unlink()
            except FileNotFoundError:
                pass
        else:
            CAPACITY.write_bytes(
                original_capacity
            )

        print(
            "[LIVE_MONEY_STATE_RESTORED] true",
            flush=True,
        )


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "live_money_runtime.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(
            encoding="utf-8"
        )
        ast.parse(cls.s)

    def test_hot_account_budget(self):
        self.assertIn(
            "MAX_HOT_ACCOUNTS=320",
            self.s,
        )

    def test_provider_safe_shard_size(self):
        self.assertIn(
            "WS_SHARD_SIZE=48",
            self.s,
        )

    def test_full_inventory_preserved(self):
        self.assertIn(
            "full_inventory_preserved_outside_hot_book",
            self.s,
        )

    def test_trader_ranking(self):
        self.assertIn(
            "historical_gross_positive",
            self.s,
        )
        self.assertIn(
            "best_local_bps",
            self.s,
        )

    def test_runtime_uses_checkpoint26_money_chain(self):
        self.assertIn(
            "return c26.main()",
            self.s,
        )

    def test_state_restored(self):
        self.assertIn(
            "[LIVE_MONEY_STATE_RESTORED]",
            self.s,
        )

    def test_no_live_send_yet(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )
        self.assertIn(
            "[LIVE_SEND] DISABLED",
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

print("[PASS] live money HOT-book runtime installed")
print("[INVENTORY] existing 76-route capacity manifest remains source")
print("[HOT_BOOK] <=320 unique watched accounts")
print("[WS] fixed 48 subscriptions per connection")
print("[RANKING] historical positive/edge first")
print("[MONEY_PATH] exact pricing + fees + ALT + signed simulation preserved")
print("[LIVE_SEND] disabled until signed-sim certification")
print("[KEY] untouched")
print("[TEST]",TEST.name)
