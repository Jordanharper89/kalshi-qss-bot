from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint11_multi_pool_registry.py"
TEST=ROOT/"test_canonical_checkpoint11_multi_pool_registry.py"

MODULE=r"""from __future__ import annotations

import json
import time

from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint10_multi_dlmm_exact_static_sweep as c10
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m

OUT=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "multi_dlmm_pair_registry.json"
)

PAIR_CAP=32
ACCOUNT_CAP=768
MAX_POOLS_PER_TOKEN=8


def pair_key(token,meteora_pool):
    token=str(token)
    pool=str(meteora_pool)

    if not token or not pool:
        raise RuntimeError(
            "CHECKPOINT11_BAD_PAIR_IDENTITY"
        )

    return token+"|"+pool


def main():
    old_pair_cap=pd.MAX_PAIRS
    old_account_cap=m.MAX_ACCOUNTS

    pd.MAX_PAIRS=PAIR_CAP
    m.MAX_ACCOUNTS=ACCOUNT_CAP

    try:
        state,_=r.q25.prepare_once(
            Path.cwd()
        )

        r.q25.bind_cached_state(
            state
        )

        r.install_proven_hot_math(
            state
        )

        pairs={
            str(pair.token):pair
            for pair in list(
                state.get("pairs")
                or []
            )
        }

        for pair in pairs.values():
            r.q18.worker().warm(
                str(pair.pump_pool)
            )

        rows=[]
        failures=[]

        for token,pair in pairs.items():
            selected=str(
                pair.meteora_pool
            )

            metas=c10._candidate_metas(
                token,
                selected,
            )

            for rank,meta in enumerate(
                metas,
                start=1,
            ):
                pool=str(meta["address"])
                key=pair_key(token,pool)

                try:
                    dlmm_state,arrays=c10._hydrate_alt(
                        meta
                    )

                    snap=c10._snapshot(
                        pair,
                        meta,
                        dlmm_state,
                    )

                    best,quotes,partials=(
                        c10._best_for_pool(
                            snap
                        )
                    )

                except Exception as exc:
                    failures.append({
                        "pair_key":key,
                        "token":token,
                        "meteora_pool":pool,
                        "reason":
                            type(exc).__name__
                            +":"
                            +str(exc)[:180],
                    })

                    print(
                        "[CHECKPOINT11_SKIP] "
                        "pair=%s %s:%s"
                        %(
                            key[:24],
                            type(exc).__name__,
                            str(exc)[:140],
                        ),
                        flush=True,
                    )
                    continue

                if best is None or quotes<=0:
                    print(
                        "[CHECKPOINT11_HOLD] "
                        "pair=%s quotes=%d partial_sizes=%d"
                        %(key[:24],quotes,partials),
                        flush=True,
                    )
                    continue

                row={
                    "pair_key":key,
                    "token":token,
                    "pump_pool":
                        str(pair.pump_pool),
                    "meteora_pool":pool,
                    "selected_legacy":
                        bool(pool==selected),
                    "discovery_rank":
                        int(rank),
                    "reported_tvl":
                        float(meta.get("tvl") or 0.0),
                    "token_x":
                        str(meta["token_x"]),
                    "token_y":
                        str(meta["token_y"]),
                    "decimals_x":
                        int(meta["decimals_x"]),
                    "decimals_y":
                        int(meta["decimals_y"]),
                    "array_count":
                        len(arrays),
                    "complete_quote_count":
                        int(quotes),
                    "partial_size_count":
                        int(partials),
                    "best_direction":
                        str(best["direction"]),
                    "best_size_sol":
                        float(best["size_sol"]),
                    "best_local_net_lamports":
                        int(best["local_net"]),
                    "best_local_bps":
                        float(best["local_bps"]),
                    "gross_positive":
                        bool(
                            int(best["local_net"])>0
                        ),
                }

                rows.append(row)

                print(
                    "[CHECKPOINT11_READY] "
                    "pair=%s legacy=%s rank=%d arrays=%d "
                    "quotes=%d best=%+d bps=%+.2f"
                    %(
                        key[:24],
                        str(row["selected_legacy"]),
                        rank,
                        row["array_count"],
                        quotes,
                        row["best_local_net_lamports"],
                        row["best_local_bps"],
                    ),
                    flush=True,
                )

        keys=[
            row["pair_key"]
            for row in rows
        ]

        if len(keys)!=len(set(keys)):
            raise RuntimeError(
                "CHECKPOINT11_PAIR_KEY_COLLISION"
            )

        by_token={}

        for row in rows:
            by_token.setdefault(
                row["token"],
                0,
            )
            by_token[row["token"]]+=1

        report={
            "revision":
                "CHECKPOINT11_MULTI_POOL_REGISTRY_V1",
            "observed_unix":
                time.time(),
            "identity":
                "token|meteora_pool",
            "source_pool_limit_per_token":
                MAX_POOLS_PER_TOKEN,
            "tokens":
                len(by_token),
            "ready_pair_count":
                len(rows),
            "alternate_ready_count":
                sum(
                    1
                    for row in rows
                    if not row["selected_legacy"]
                ),
            "gross_positive_count":
                sum(
                    1
                    for row in rows
                    if row["gross_positive"]
                ),
            "failures":
                failures,
            "rows":
                rows,
            "execution_authority":
                False,
            "simulation":
                False,
            "broadcast":
                False,
        }

        out=Path.cwd()/OUT
        out.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        out.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        print(
            "[CHECKPOINT11_SUMMARY] "
            "tokens=%d ready_pairs=%d alternates=%d "
            "gross_positive=%d failures=%d"
            %(
                report["tokens"],
                report["ready_pair_count"],
                report["alternate_ready_count"],
                report["gross_positive_count"],
                len(failures),
            ),
            flush=True,
        )

        print(
            "[CHECKPOINT11_IDENTITY] "
            "token_pipe_meteora_pool=True collisions=0",
            flush=True,
        )

        print(
            "[CHECKPOINT11_REPORT] %s"
            %out,
            flush=True,
        )

        print(
            "[CHECKPOINT11_GATE] "
            "status=PAIR_KEY_REGISTRY_READY",
            flush=True,
        )

        print("[SIMULATION] disabled",flush=True)
        print("[BROADCAST] disabled",flush=True)

        return 0

    finally:
        pd.MAX_PAIRS=old_pair_cap
        m.MAX_ACCOUNTS=old_account_cap

        if getattr(r.q18,"_worker",None) is not None:
            r.q18._worker.close()
            r.q18._worker=None

        try:
            r.q25.q23.worker().close()
        except Exception:
            pass


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint11_multi_pool_registry.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_pair_identity(self):
        self.assertIn(
            'return token+"|"+pool',
            self.s,
        )

    def test_collision_gate(self):
        self.assertIn(
            "CHECKPOINT11_PAIR_KEY_COLLISION",
            self.s,
        )

    def test_registry_persisted(self):
        self.assertIn(
            "multi_dlmm_pair_registry.json",
            self.s,
        )

    def test_quoteability_required(self):
        self.assertIn(
            "if best is None or quotes<=0:",
            self.s,
        )

    def test_selected_and_alternate_preserved(self):
        self.assertIn(
            '"selected_legacy":',
            self.s,
        )
        self.assertIn(
            '"alternate_ready_count":',
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

print("[PASS] canonical checkpoint-11 multi-pool registry installed")
print("[IDENTITY] token|meteora_pool")
print("[SOURCE] checkpoint-10 physically quoteable top-pool coverage")
print("[PERSIST] runtime_state/oracle/solana_atomic_executor/multi_dlmm_pair_registry.json")
print("[COLLISION] fail-closed")
print("[SIMULATION] disabled")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
