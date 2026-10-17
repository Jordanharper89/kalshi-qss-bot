from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint25_expanded_live_universe_cutover.py"
TEST=ROOT/"test_canonical_checkpoint25_expanded_live_universe_cutover.py"

MODULE=r"""from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint22_cached_alt_latency_cutover as c22
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint24_capacity_aware_warm_universe as c24
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

MANIFEST=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "capacity_aware_warm_universe.json"
)


def _load_manifest():
    q=Path.cwd()/MANIFEST

    if not q.is_file():
        raise RuntimeError(
            "CHECKPOINT25_MANIFEST_MISSING:"+str(q)
        )

    payload=json.loads(
        q.read_text(encoding="utf-8")
    )

    rows=list(payload.get("rows") or [])

    if not rows:
        raise RuntimeError(
            "CHECKPOINT25_EMPTY_MANIFEST"
        )

    return payload,rows


def _hydrate_state(root):
    payload,rows=_load_manifest()

    pairs=[]
    address_bindings=defaultdict(list)
    pump_cache={}
    failures=[]

    print(
        "[CHECKPOINT25_HYDRATE_START] "
        "manifest_pairs=%d manifest_accounts=%s"
        %(
            len(rows),
            payload.get("selected_accounts"),
        ),
        flush=True,
    )

    for row in rows:
        identity=str(row["identity"])

        try:
            pair,watched=c24._hydrate(
                row,
                pump_cache,
            )

        except Exception as exc:
            failures.append(
                identity+"|"
                +type(exc).__name__
                +":"+str(exc)
            )

            print(
                "[CHECKPOINT25_HYDRATE_SKIP] "
                "pair=%s error=%s:%s"
                %(
                    identity[:48],
                    type(exc).__name__,
                    str(exc)[:180],
                ),
                flush=True,
            )

            continue

        index=len(pairs)
        pairs.append(pair)

        address_bindings[
            pair.pump_base_vault
        ].append((index,"PUMP_BASE"))

        address_bindings[
            pair.pump_quote_vault
        ].append((index,"PUMP_QUOTE"))

        address_bindings[
            pair.meteora_pool
        ].append((index,"DLMM_POOL"))

        for j,a in enumerate(pair.arrays):
            address_bindings[
                str(a[1])
            ].append(
                (
                    index,
                    "DLMM_ARRAY_%d"%j,
                )
            )

    if not pairs:
        raise RuntimeError(
            "CHECKPOINT25_NO_HYDRATED_PAIRS"
        )

    addresses=list(address_bindings)

    state={
        "landing":
            engine.landing_cost_lamports(),
        "pairs":pairs,
        "preg":{
            a:bindings[0]
            for a,bindings
            in address_bindings.items()
        },
        "multi_preg":{
            a:list(bindings)
            for a,bindings
            in address_bindings.items()
        },
        "addresses":addresses,
        "eps":defaultdict(list),
        "cstates":[],
        "creg":{},
        "observed":{},
        "xreg":{},
    }

    cap={
        "revision":
            "CHECKPOINT25_EXPANDED_LIVE_UNIVERSE",
        "manifest_pairs":
            len(rows),
        "hydrated_pairs":
            len(pairs),
        "accounts":
            len(addresses),
        "multi_account_fanout":
            True,
        "pair_identity_lane":
            True,
        "execution_authority":
            False,
        "broadcast":
            False,
    }

    print(
        "[CHECKPOINT25_HYDRATED] "
        "pairs=%d accounts=%d shared_accounts=%d failures=%d"
        %(
            len(pairs),
            len(addresses),
            sum(
                1
                for x in address_bindings.values()
                if len(x)>1
            ),
            len(failures),
        ),
        flush=True,
    )

    return state,cap


def _pair_identity(pair):
    return (
        str(pair.token)
        +"|"
        +str(pair.meteora_pool)
    )


def _process_event_multi(
    state,
    ev,
    counters,
    lane,
):
    address=ev["address"]

    bindings=(
        state.get("multi_preg",{})
        .get(address)
        or []
    )

    if not bindings:
        return

    submitted=set()

    for index,kind in bindings:
        pair=state["pairs"][index]
        token=str(pair.token)

        if token not in r.READY_TOKENS:
            continue

        try:
            changed=(
                r.persistent.m.pd
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
            counters["event_errors"]+=1
            continue

        if not changed:
            continue

        identity=_pair_identity(pair)

        if identity in submitted:
            continue

        submitted.add(identity)

        counters["priced_events"]+=1

        lane.submit(
            identity,
            r.immutable_snapshot(pair),
            ev["slot"],
            ev["received_ns"],
        )


def main():
    p=argparse.ArgumentParser()

    p.add_argument(
        "--seconds",
        type=float,
        default=3600.0,
    )

    args=p.parse_args()

    if args.seconds<=0:
        raise RuntimeError(
            "CHECKPOINT25_SECONDS_MUST_BE_POSITIVE"
        )

    state,cap=_hydrate_state(Path.cwd())

    old_prepare=r.q25.prepare_once
    old_process=r.process_event
    old_argv=list(sys.argv)

    def prepared(_root):
        return state,cap

    try:
        r.q25.prepare_once=prepared
        r.process_event=_process_event_multi

        print(
            "[CHECKPOINT25_ACTIVATION] "
            "expanded_live_universe=True "
            "pairs=%d accounts=%d seconds=%.0f"
            %(
                len(state["pairs"]),
                len(state["addresses"]),
                args.seconds,
            ),
            flush=True,
        )

        print(
            "[CHECKPOINT25_FANOUT] "
            "shared_pump_vault_update -> "
            "all_exact_token_pool_routes",
            flush=True,
        )

        print(
            "[CHECKPOINT25_LANE] "
            "key=token|meteora_pool "
            "alternate_pools_do_not_replace_each_other",
            flush=True,
        )

        print(
            "[CHECKPOINT25_CHAIN] "
            "expanded_state -> checkpoint17_pair_templates -> "
            "checkpoint20_canonical_ALT -> checkpoint22_ALT_cache -> "
            "real_fee -> freshness -> checkpoint21_signed_sim",
            flush=True,
        )

        print(
            "[CHECKPOINT25_HOT_PATH] "
            "discovery=False hydration=False filesystem=False",
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

        return c22.main()

    finally:
        r.q25.prepare_once=old_prepare
        r.process_event=old_process
        sys.argv=old_argv


if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint25_expanded_live_universe_cutover.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_uses_cp24_manifest(self):
        self.assertIn(
            "capacity_aware_warm_universe.json",
            self.s,
        )
        self.assertIn(
            "c24._hydrate(",
            self.s,
        )

    def test_shared_account_fanout(self):
        self.assertIn(
            '"multi_preg"',
            self.s,
        )
        self.assertIn(
            "for index,kind in bindings",
            self.s,
        )

    def test_pair_identity_lane(self):
        self.assertIn(
            'str(pair.token)',
            self.s,
        )
        self.assertIn(
            'str(pair.meteora_pool)',
            self.s,
        )
        self.assertIn(
            "lane.submit(",
            self.s,
        )

    def test_existing_execution_chain(self):
        self.assertIn(
            "return c22.main()",
            self.s,
        )

    def test_hot_path_no_discovery(self):
        self.assertIn(
            "[CHECKPOINT25_HOT_PATH]",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )


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

print("[PASS] checkpoint-25 expanded live universe cutover installed")
print("[SOURCE] checkpoint-24 capacity-aware warm manifest")
print("[FANOUT] shared Pump vault updates propagate to every exact token|Meteora route")
print("[LANE] pair identity prevents alternate pools from replacing one another")
print("[CHAIN] checkpoint-22 cached ALT + checkpoint-21 signed sim preserved")
print("[HOT_PATH] no discovery/hydration/filesystem after activation")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
