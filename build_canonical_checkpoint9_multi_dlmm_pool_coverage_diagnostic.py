from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint9_multi_dlmm_pool_coverage_diagnostic.py"
TEST=ROOT/"test_canonical_checkpoint9_multi_dlmm_pool_coverage_diagnostic.py"

MODULE=r"""from __future__ import annotations

import time
import urllib.error
import urllib.parse

from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c


def _mint(value):
    if isinstance(value,str):
        return value

    if isinstance(value,dict):
        return (
            value.get("address")
            or value.get("mint")
            or value.get("token_address")
        )

    return None


def _all_ws_sol_pools(token):
    url=(
        "https://dlmm.datapi.meteora.ag/pools"
        "?page=1&page_size=100&query="
        +urllib.parse.quote(str(token))
    )

    last=None

    for attempt in range(6):
        try:
            payload=c.http(url)
            break
        except urllib.error.HTTPError as exc:
            last=exc

            if getattr(exc,"code",None)!=429:
                raise

            delay=min(
                6.0,
                .50*(2**attempt),
            )

            print(
                "[CHECKPOINT9_429] "
                "token=%s attempt=%d sleep=%.2fs"
                %(
                    str(token)[:10],
                    attempt+1,
                    delay,
                ),
                flush=True,
            )

            time.sleep(delay)
    else:
        raise last or RuntimeError(
            "CHECKPOINT9_METEORA_DISCOVERY_EXHAUSTED"
        )

    rows=(
        payload.get("data")
        if isinstance(payload,dict)
        else payload
    )

    found=[]

    for raw in rows or []:
        tx=raw.get("token_x") or raw.get("tokenX") or {}
        ty=raw.get("token_y") or raw.get("tokenY") or {}

        mx=_mint(tx)
        my=_mint(ty)

        if {mx,my}!={c.WSOL,str(token)}:
            continue

        address=(
            raw.get("address")
            or raw.get("pool_address")
            or raw.get("pubkey")
        )

        if not address:
            continue

        try:
            tvl=float(
                raw.get("tvl")
                or raw.get("liquidity")
                or raw.get("liquidity_usd")
                or 0
            )
        except Exception:
            tvl=0.0

        dx=(
            int(tx.get("decimals",9))
            if isinstance(tx,dict)
            else 9
        )

        dy=(
            int(ty.get("decimals",6))
            if isinstance(ty,dict)
            else 6
        )

        found.append({
            "address":str(address),
            "token_x":mx,
            "token_y":my,
            "decimals_x":dx,
            "decimals_y":dy,
            "tvl":tvl,
        })

    unique={}

    for row in found:
        address=row["address"]

        if (
            address not in unique
            or row["tvl"]>unique[address]["tvl"]
        ):
            unique[address]=row

    return sorted(
        unique.values(),
        key=lambda x:x["tvl"],
        reverse=True,
    )


def main():
    root=Path.cwd()

    selected=engine.candidate_universe(
        root
    )

    if not selected:
        raise RuntimeError(
            "CHECKPOINT9_NO_CURRENT_CROSSLIST"
        )

    print(
        "[CHECKPOINT9_START] "
        "selected_tokens=%d"
        %len(selected),
        flush=True,
    )

    total=0
    alternates=0
    multi_tokens=0
    missing_selected=0

    for item in selected:
        token=str(item["token"])
        selected_pool=str(
            item["meteora_pool"]
        )

        pools=_all_ws_sol_pools(
            token
        )

        total+=len(pools)

        addresses={
            row["address"]
            for row in pools
        }

        if selected_pool not in addresses:
            missing_selected+=1

        alt=max(
            0,
            len(pools)-1,
        )

        alternates+=alt

        if len(pools)>1:
            multi_tokens+=1

        print(
            "[CHECKPOINT9_TOKEN] "
            "token=%s pools=%d alternates=%d "
            "selected=%s selected_present=%s"
            %(
                token[:12],
                len(pools),
                alt,
                selected_pool[:12],
                str(
                    selected_pool in addresses
                ),
            ),
            flush=True,
        )

        for rank,row in enumerate(
            pools,
            start=1,
        ):
            print(
                "[CHECKPOINT9_POOL] "
                "token=%s rank=%d pool=%s tvl=%.6f "
                "currently_selected=%s"
                %(
                    token[:10],
                    rank,
                    row["address"],
                    row["tvl"],
                    str(
                        row["address"]
                        ==selected_pool
                    ),
                ),
                flush=True,
            )

    print(
        "[CHECKPOINT9_SUMMARY] "
        "tokens=%d dlmm_pools=%d "
        "alternate_pools=%d multi_pool_tokens=%d "
        "selected_missing=%d"
        %(
            len(selected),
            total,
            alternates,
            multi_tokens,
            missing_selected,
        ),
        flush=True,
    )

    if alternates:
        print(
            "[CHECKPOINT9_GATE] "
            "status=MULTI_DLMM_EXPANSION_REQUIRED",
            flush=True,
        )
    else:
        print(
            "[CHECKPOINT9_GATE] "
            "status=SINGLE_POOL_COVERAGE_COMPLETE",
            flush=True,
        )

    print(
        "[SCOPE] discovery_diagnostic_only=True",
        flush=True,
    )
    print("[RPC_HYDRATION] disabled",flush=True)
    print("[SIMULATION] disabled",flush=True)
    print("[BROADCAST] disabled",flush=True)

    return 0


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint9_multi_dlmm_pool_coverage_diagnostic.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_page_size_100(self):
        self.assertIn(
            "page=1&page_size=100",
            self.s,
        )

    def test_exact_wsol_pair_filter(self):
        self.assertIn(
            "if {mx,my}!={c.WSOL,str(token)}:",
            self.s,
        )

    def test_all_pools_not_best_only(self):
        self.assertIn(
            "return sorted(",
            self.s,
        )
        self.assertNotIn(
            "best=(",
            self.s,
        )

    def test_selected_pool_comparison(self):
        self.assertIn(
            "currently_selected=",
            self.s,
        )
        self.assertIn(
            "alternate_pools=",
            self.s,
        )

    def test_bounded_429(self):
        self.assertIn(
            "for attempt in range(6):",
            self.s,
        )

    def test_no_execution(self):
        self.assertNotIn(
            "simulateTransaction",
            self.s,
        )
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] canonical checkpoint-9 multi-DLMM coverage diagnostic installed")
print("[SCOPE] every WSOL DLMM pool for each current Pump crosslisted token")
print("[COMPARE] selected highest-TVL pool vs all alternates")
print("[RPC_HYDRATION] disabled")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[SIMULATION] disabled")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
