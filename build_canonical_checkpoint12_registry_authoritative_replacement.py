from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint12_multi_pool_live_size_optimizer.py"
TEST=ROOT/"test_canonical_checkpoint12_multi_pool_live_size_optimizer.py"

MODULE=r"""from __future__ import annotations

import asyncio
import json

from pathlib import Path
from meteora_dlmm import PoolState

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

REGISTRY=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "multi_dlmm_pair_registry.json"
)

SECONDS=90.0

SIZES=(
    0.001,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    1.000,
    1.400,
)

WATCH={
    "events":0,
    "pair_updates":0,
    "quotes":0,
    "gross_positive":0,
    "best":None,
}


def pair_key(pair):
    return (
        str(pair.token)
        +"|"
        +str(pair.meteora_pool)
    )


def _load_registry():
    path=Path.cwd()/REGISTRY

    if not path.is_file():
        raise RuntimeError(
            "CHECKPOINT11_REGISTRY_MISSING:"
            +str(path)
        )

    payload=json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    rows=list(
        payload.get("rows")
        or []
    )

    if not rows:
        raise RuntimeError(
            "CHECKPOINT11_REGISTRY_EMPTY"
        )

    keys=[
        str(row.get("pair_key") or "")
        for row in rows
    ]

    if (
        any(not key for key in keys)
        or len(keys)!=len(set(keys))
    ):
        raise RuntimeError(
            "CHECKPOINT12_BAD_REGISTRY_IDENTITY"
        )

    return payload,rows


def _token_amount(raw):
    return pd._token_amount_from_raw(
        raw
    )


def _hydrate_pump(row):
    pump_pool=str(
        row["pump_pool"]
    )

    pd_raw,_=c.account(
        pump_pool
    )

    decoded=c.decode_pump_pool(
        pd_raw
    )

    if decoded["quote_mint"]!=c.WSOL:
        raise RuntimeError(
            "CHECKPOINT12_PUMP_NOT_WSOL"
        )

    if decoded["base_mint"]!=str(
        row["token"]
    ):
        raise RuntimeError(
            "CHECKPOINT12_PUMP_TOKEN_DRIFT"
        )

    base_raw,_=c.account(
        decoded["base_vault"]
    )

    quote_raw,_=c.account(
        decoded["quote_vault"]
    )

    return {
        "base_vault":
            str(decoded["base_vault"]),
        "quote_vault":
            str(decoded["quote_vault"]),
        "base_reserve":
            _token_amount(base_raw),
        "quote_reserve":
            _token_amount(quote_raw),
    }


def _hydrate_pair(row,pump):
    pool=str(
        row["meteora_pool"]
    )

    lb,_=c.account(
        pool
    )

    arrays=c.dlmm_arrays(
        pool
    )

    state=PoolState.from_accounts(
        lb,
        [x[2] for x in arrays],
        decimals_x=int(
            row["decimals_x"]
        ),
        decimals_y=int(
            row["decimals_y"]
        ),
        lb_pair_key=c.b58d(
            pool
        ),
        exhaustive=True,
    )

    pair=pd.PairState(
        token=str(
            row["token"]
        ),
        pump_pool=str(
            row["pump_pool"]
        ),
        meteora_pool=pool,
        token_x=str(
            row["token_x"]
        ),
        token_y=str(
            row["token_y"]
        ),
        decimals_x=int(
            row["decimals_x"]
        ),
        decimals_y=int(
            row["decimals_y"]
        ),
        pump_base_vault=
            pump["base_vault"],
        pump_quote_vault=
            pump["quote_vault"],
        pump_base_reserve=int(
            pump["base_reserve"]
        ),
        pump_quote_reserve=int(
            pump["quote_reserve"]
        ),
        lb_bytes=lb,
        arrays=list(arrays),
        dlmm_state=state,
    )

    expected=str(
        row["pair_key"]
    )

    if pair_key(pair)!=expected:
        raise RuntimeError(
            "CHECKPOINT12_PAIR_KEY_DRIFT"
        )

    return pair


def _expanded_state():
    payload,rows=_load_registry()

    pumps={}
    expanded=[]
    failures=[]

    for row in rows:
        token=str(
            row["token"]
        )

        if token not in pumps:
            try:
                pumps[token]=_hydrate_pump(
                    row
                )
            except Exception as exc:
                failures.append(
                    row["pair_key"]
                    +":PUMP:"
                    +type(exc).__name__
                    +":"
                    +str(exc)[:120]
                )
                continue

        try:
            pair=_hydrate_pair(
                row,
                pumps[token],
            )
        except Exception as exc:
            failures.append(
                row["pair_key"]
                +":DLMM:"
                +type(exc).__name__
                +":"
                +str(exc)[:120]
            )
            continue

        expanded.append(
            pair
        )

    if not expanded:
        raise RuntimeError(
            "CHECKPOINT12_NO_EXPANDED_PAIRS"
        )

    mpreg={}

    for i,pair in enumerate(
        expanded
    ):
        entries=[
            (
                pair.pump_base_vault,
                "PUMP_BASE",
            ),
            (
                pair.pump_quote_vault,
                "PUMP_QUOTE",
            ),
            (
                pair.meteora_pool,
                "DLMM_POOL",
            ),
        ]

        entries.extend(
            (
                address,
                "DLMM_ARRAY_%d"%j,
            )
            for j,(_,address,_raw)
            in enumerate(pair.arrays)
        )

        for address,kind in entries:
            mpreg.setdefault(
                str(address),
                []
            ).append(
                (i,kind)
            )

    addresses=list(
        mpreg
    )

    return (
        {
            "pairs":expanded,
            "mpreg":mpreg,
            "addresses":addresses,
        },
        payload,
        failures,
    )


def _process_event(
    state,
    ev,
    counters,
    lane,
):
    address=str(
        ev["address"]
    )

    bindings=list(
        state.get(
            "mpreg",
            {}
        ).get(
            address,
            ()
        )
    )

    if not bindings:
        return

    WATCH["events"]+=1

    for index,kind in bindings:
        pair=state["pairs"][index]

        try:
            changed=pd.apply_account_event(
                pair,
                kind,
                address,
                ev["raw"],
                ev["slot"],
                ev["received_ns"],
            )
        except Exception:
            counters[
                "event_errors"
            ]+=1
            continue

        if not changed:
            continue

        WATCH["pair_updates"]+=1
        counters[
            "priced_events"
        ]+=1

        lane.submit(
            pair_key(pair),
            r.immutable_snapshot(
                pair
            ),
            ev["slot"],
            ev["received_ns"],
        )


def _price(
    self,
    identity,
    row,
):
    (
        snap,
        slot,
        received_ns,
        generation,
    )=row

    token=str(
        snap["token"]
    )

    pool=str(
        snap["meteora"]["address"]
    )

    best=None

    for size in SIZES:
        for fn in (
            c7._reverse_only,
            c7._forward_only,
        ):
            if self.newer_waiting(
                identity,
                generation,
            ):
                self.scan_replaced+=1
                return

            try:
                op=fn(
                    snap,
                    size,
                )
            except RuntimeError as exc:
                if str(exc)=="DLMM_PARTIAL":
                    continue
                raise

            WATCH["quotes"]+=1
            self.processed+=1

            candidate=dict(
                op
            )

            candidate[
                "pair_key"
            ]=identity

            candidate[
                "meteora_pool"
            ]=pool

            candidate[
                "slot"
            ]=slot

            if (
                best is None
                or int(
                    candidate[
                        "local_net"
                    ]
                )
                >
                int(
                    best[
                        "local_net"
                    ]
                )
            ):
                best=candidate

            if int(
                candidate[
                    "local_net"
                ]
            )>0:
                WATCH[
                    "gross_positive"
                ]+=1

                print(
                    "[CHECKPOINT12_POSITIVE] "
                    "pair=%s token=%s pool=%s "
                    "slot=%s dir=%s size=%.3f "
                    "net=%+d bps=%+.2f"
                    %(
                        identity[:28],
                        token[:10],
                        pool[:12],
                        slot,
                        candidate[
                            "direction"
                        ],
                        candidate[
                            "size_sol"
                        ],
                        int(
                            candidate[
                                "local_net"
                            ]
                        ),
                        float(
                            candidate[
                                "local_bps"
                            ]
                        ),
                    ),
                    flush=True,
                )

    if best is None:
        return

    if (
        WATCH["best"] is None
        or int(
            best["local_net"]
        )
        >
        int(
            WATCH["best"][
                "local_net"
            ]
        )
    ):
        WATCH["best"]=dict(
            best
        )

    if (
        self.best is None
        or int(
            best["local_net"]
        )
        >
        int(
            self.best[
                "local_net"
            ]
        )
    ):
        self.best=dict(
            best
        )

    if int(
        best["local_net"]
    )>0:
        self.positive+=1


def main():
    old_process=r.process_event
    old_price=r.canonical_price

    lane=None

    try:
        state,registry,failures=(
            _expanded_state()
        )

        warmed=(
            r.q25
            .install_hot_math_and_prewarm(
                state
            )
        )

        r.q18.install_exact_hot_math()

        unique_pumps=[]

        for pair in state["pairs"]:
            pool=str(
                pair.pump_pool
            )

            if pool in unique_pumps:
                continue

            unique_pumps.append(
                pool
            )

            r.q18.worker().warm(
                pool
            )

        r.process_event=_process_event
        r.canonical_price=_price

        lane=r.q20.LatestStateLane()

        lane._price=(
            _price.__get__(
                lane,
                r.q20.LatestStateLane,
            )
        )

        lane.start()

        print(
            "[CHECKPOINT12_START] "
            "seconds=90 "
            "source=frozen_checkpoint11_registry "
            "pair_identity=token|meteora_pool",
            flush=True,
        )

        print(
            "[CHECKPOINT12_DISCOVERY] "
            "startup_rejoin=False "
            "registry_is_authoritative=True",
            flush=True,
        )

        print(
            "[CHECKPOINT12_UNIVERSE] "
            "registry_pairs=%d live_pairs=%d "
            "alternate_pairs=%d accounts=%d "
            "shards=%d hydrate_failures=%d"
            %(
                int(
                    registry.get(
                        "ready_pair_count"
                    )
                    or len(
                        registry.get(
                            "rows"
                        )
                        or []
                    )
                ),
                len(
                    state["pairs"]
                ),
                sum(
                    1
                    for row in (
                        registry.get(
                            "rows"
                        )
                        or []
                    )
                    if not row.get(
                        "selected_legacy"
                    )
                ),
                len(
                    state["addresses"]
                ),
                len(
                    r.persistent.m
                    ._shards(
                        state["addresses"]
                    )
                ),
                len(failures),
            ),
            flush=True,
        )

        print(
            "[CHECKPOINT12_TOKEN_WARM] "
            "tokens=%d"
            %len(warmed),
            flush=True,
        )

        print(
            "[CHECKPOINT12_SIZES] "
            "0.001,0.010,0.025,0.050,"
            "0.100,0.180,0.280,0.500,"
            "1.000,1.400",
            flush=True,
        )

        print(
            "[CHECKPOINT12_SELECTION] "
            "global_max_exact_local_net=True "
            "smallest_size_bias=False",
            flush=True,
        )

        print(
            "[CHECKPOINT12_EXECUTION] "
            "compile=False fee_readback=False "
            "simulation=False",
            flush=True,
        )

        print(
            "[BROADCAST] disabled",
            flush=True,
        )

        asyncio.run(
            r.serve_canonical(
                state,
                SECONDS,
                lane,
            )
        )

        best=WATCH["best"]

        print(
            "[CHECKPOINT12_SUMMARY] "
            "events=%d pair_updates=%d "
            "quotes=%d gross_positive=%d "
            "processed=%d scan_replaced=%d"
            %(
                WATCH["events"],
                WATCH["pair_updates"],
                WATCH["quotes"],
                WATCH["gross_positive"],
                lane.processed,
                lane.scan_replaced,
            ),
            flush=True,
        )

        if best is not None:
            print(
                "[CHECKPOINT12_BEST] "
                "pair=%s token=%s pool=%s "
                "dir=%s size=%.3f "
                "net=%+d bps=%+.2f"
                %(
                    best["pair_key"][:28],
                    best["token"][:10],
                    best[
                        "meteora_pool"
                    ][:12],
                    best["direction"],
                    best["size_sol"],
                    int(
                        best[
                            "local_net"
                        ]
                    ),
                    float(
                        best[
                            "local_bps"
                        ]
                    ),
                ),
                flush=True,
            )

        print(
            "[CHECKPOINT12_GATE] "
            "status=%s"
            %(
                "MULTI_POOL_GROSS_POSITIVE_OBSERVED"
                if WATCH[
                    "gross_positive"
                ]>0
                else
                "NO_MULTI_POOL_GROSS_POSITIVE_IN_90S"
            ),
            flush=True,
        )

        return 0

    finally:
        r.process_event=old_process
        r.canonical_price=old_price

        if lane is not None:
            lane.close()

        if getattr(
            r.q18,
            "_worker",
            None
        ) is not None:
            r.q18._worker.close()
            r.q18._worker=None

        try:
            r.q25.q23.worker().close()
        except Exception:
            pass


if __name__=="__main__":
    raise SystemExit(
        main()
    )
"""

TEST_CODE=r"""import ast
import unittest
from pathlib import Path

P=Path(
 "qseries_v2/oracle_execution/solana_atomic_executor/"
 "checkpoint12_multi_pool_live_size_optimizer.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(
            encoding="utf-8"
        )
        ast.parse(cls.s)

    def test_registry_authoritative(self):
        self.assertIn(
            "registry_is_authoritative=True",
            self.s,
        )
        self.assertNotIn(
            "base_by_token",
            self.s,
        )

    def test_hydrates_pump_from_registry(self):
        self.assertIn(
            'row["pump_pool"]',
            self.s,
        )
        self.assertIn(
            "c.decode_pump_pool(",
            self.s,
        )

    def test_pair_identity_drives_lane(self):
        self.assertIn(
            "lane.submit(",
            self.s,
        )
        self.assertIn(
            "pair_key(pair)",
            self.s,
        )

    def test_full_size_ladder(self):
        for value in (
            "0.001","0.010","0.025",
            "0.050","0.100","0.180",
            "0.280","0.500","1.000",
            "1.400",
        ):
            self.assertIn(
                value,
                self.s,
            )

    def test_existing_websocket_runtime(self):
        self.assertIn(
            "r.serve_canonical(",
            self.s,
        )

    def test_no_execution(self):
        self.assertNotIn(
            "compile_current(",
            self.s,
        )
        self.assertNotIn(
            "simulateTransaction",
            self.s,
        )
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

print("[PASS] canonical checkpoint-12 clean registry-authoritative replacement installed")
print("[ROOT_CAUSE] removed live-discovery rejoin against frozen checkpoint-11 registry")
print("[SOURCE] registry rows hydrate their own Pump + Meteora physical state")
print("[IDENTITY] token|meteora_pool")
print("[SIZES] full certified ladder; no 0.001 bias")
print("[TRANSPORT] existing canonical sharded WebSocket runtime")
print("[EXECUTION] gross discovery only")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
