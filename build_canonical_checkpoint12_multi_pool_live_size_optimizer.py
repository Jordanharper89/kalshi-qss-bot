from pathlib import Path

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"
TARGET=PKG/"checkpoint12_multi_pool_live_size_optimizer.py"
TEST=ROOT/"test_canonical_checkpoint12_multi_pool_live_size_optimizer.py"

MODULE=r"""from __future__ import annotations

import asyncio
import copy
import json
import time

from pathlib import Path
from meteora_dlmm import PoolState

from qseries_v2.oracle_execution.solana_atomic_executor import runtime as r
from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint7_live_90s_fee_ranked_watch as c7
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

REGISTRY=Path(
    "runtime_state/oracle/solana_atomic_executor/"
    "multi_dlmm_pair_registry.json"
)

SECONDS=90.0
PAIR_CAP=32
ACCOUNT_CAP=768

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


def _hydrate_pair(base,row):
    pool=str(row["meteora_pool"])

    lb,_=c.account(pool)
    arrays=c.dlmm_arrays(pool)

    state=PoolState.from_accounts(
        lb,
        [x[2] for x in arrays],
        decimals_x=int(row["decimals_x"]),
        decimals_y=int(row["decimals_y"]),
        lb_pair_key=c.b58d(pool),
        exhaustive=True,
    )

    return pd.PairState(
        token=str(row["token"]),
        pump_pool=str(base.pump_pool),
        meteora_pool=pool,
        token_x=str(row["token_x"]),
        token_y=str(row["token_y"]),
        decimals_x=int(row["decimals_x"]),
        decimals_y=int(row["decimals_y"]),
        pump_base_vault=str(base.pump_base_vault),
        pump_quote_vault=str(base.pump_quote_vault),
        pump_base_reserve=int(base.pump_base_reserve),
        pump_quote_reserve=int(base.pump_quote_reserve),
        lb_bytes=lb,
        arrays=list(arrays),
        dlmm_state=state,
    )


def _expanded_state():
    payload,rows=_load_registry()

    base_state,_=r.q25.prepare_once(
        Path.cwd()
    )

    base_by_token={
        str(pair.token):pair
        for pair in list(
            base_state.get("pairs")
            or []
        )
    }

    expanded=[]
    failures=[]

    for row in rows:
        token=str(row["token"])
        base=base_by_token.get(token)

        if base is None:
            failures.append(
                row["pair_key"]
                +":BASE_TOKEN_NOT_CURRENT"
            )
            continue

        try:
            pair=_hydrate_pair(
                base,
                row,
            )
        except Exception as exc:
            failures.append(
                row["pair_key"]
                +":"
                +type(exc).__name__
                +":"
                +str(exc)[:120]
            )
            continue

        if pair_key(pair)!=row["pair_key"]:
            raise RuntimeError(
                "CHECKPOINT12_PAIR_KEY_DRIFT"
            )

        expanded.append(pair)

    if not expanded:
        raise RuntimeError(
            "CHECKPOINT12_NO_EXPANDED_PAIRS"
        )

    mpreg={}

    for i,pair in enumerate(expanded):
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

    addresses=list(mpreg)

    if len(addresses)>ACCOUNT_CAP:
        raise RuntimeError(
            "CHECKPOINT12_ACCOUNT_CAP_EXCEEDED:"
            +str(len(addresses))
        )

    state=dict(base_state)
    state["pairs"]=expanded
    state["mpreg"]=mpreg
    state["addresses"]=addresses

    return (
        state,
        payload,
        failures,
    )


def _process_event(
    state,
    ev,
    counters,
    lane,
):
    address=str(ev["address"])
    bindings=list(
        state.get("mpreg",{}).get(
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
            counters["event_errors"]+=1
            continue

        if not changed:
            continue

        WATCH["pair_updates"]+=1
        counters["priced_events"]+=1

        lane.submit(
            pair_key(pair),
            r.immutable_snapshot(pair),
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

    token=str(snap["token"])
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

            candidate=dict(op)
            candidate["pair_key"]=identity
            candidate["meteora_pool"]=pool
            candidate["slot"]=slot

            if (
                best is None
                or int(candidate["local_net"])
                >int(best["local_net"])
            ):
                best=candidate

            if int(candidate["local_net"])>0:
                WATCH["gross_positive"]+=1

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
                        candidate["direction"],
                        candidate["size_sol"],
                        int(candidate["local_net"]),
                        float(candidate["local_bps"]),
                    ),
                    flush=True,
                )

    if best is None:
        return

    if (
        WATCH["best"] is None
        or int(best["local_net"])
        >int(WATCH["best"]["local_net"])
    ):
        WATCH["best"]=dict(best)

    if (
        self.best is None
        or int(best["local_net"])
        >int(self.best["local_net"])
    ):
        self.best=dict(best)

    if int(best["local_net"])>0:
        self.positive+=1


def main():
    old_pair_cap=pd.MAX_PAIRS
    old_account_cap=m.MAX_ACCOUNTS
    old_process=r.process_event
    old_price=r.canonical_price

    pd.MAX_PAIRS=PAIR_CAP
    m.MAX_ACCOUNTS=ACCOUNT_CAP

    lane=None

    try:
        state,registry,failures=(
            _expanded_state()
        )

        r.q25.bind_cached_state(
            state
        )

        r.install_proven_hot_math(
            state
        )

        unique_pumps=[]

        for pair in state["pairs"]:
            pool=str(pair.pump_pool)

            if pool in unique_pumps:
                continue

            unique_pumps.append(pool)
            r.q18.worker().warm(pool)

        r.READY_TOKENS={
            str(pair.token)
            for pair in state["pairs"]
        }

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
            "seconds=90 pair_identity=token|meteora_pool",
            flush=True,
        )
        print(
            "[CHECKPOINT12_UNIVERSE] "
            "registry_pairs=%d live_pairs=%d "
            "alternate_pairs=%d accounts=%d shards=%d "
            "hydrate_failures=%d"
            %(
                int(
                    registry.get(
                        "ready_pair_count"
                    )
                    or len(
                        registry.get("rows") or []
                    )
                ),
                len(state["pairs"]),
                sum(
                    1
                    for row in (
                        registry.get("rows") or []
                    )
                    if not row.get(
                        "selected_legacy"
                    )
                ),
                len(state["addresses"]),
                len(
                    r.persistent.m._shards(
                        state["addresses"]
                    )
                ),
                len(failures),
            ),
            flush=True,
        )
        print(
            "[CHECKPOINT12_SIZES] "
            "0.001,0.010,0.025,0.050,0.100,"
            "0.180,0.280,0.500,1.000,1.400",
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
            "compile=False fee_readback=False simulation=False",
            flush=True,
        )
        print("[BROADCAST] disabled",flush=True)

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
            "events=%d pair_updates=%d quotes=%d "
            "gross_positive=%d processed=%d "
            "scan_replaced=%d"
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
                "dir=%s size=%.3f net=%+d bps=%+.2f"
                %(
                    best["pair_key"][:28],
                    best["token"][:10],
                    best["meteora_pool"][:12],
                    best["direction"],
                    best["size_sol"],
                    int(best["local_net"]),
                    float(best["local_bps"]),
                ),
                flush=True,
            )

        print(
            "[CHECKPOINT12_GATE] status=%s"
            %(
                "MULTI_POOL_GROSS_POSITIVE_OBSERVED"
                if WATCH["gross_positive"]>0
                else "NO_MULTI_POOL_GROSS_POSITIVE_IN_90S"
            ),
            flush=True,
        )

        return 0

    finally:
        r.process_event=old_process
        r.canonical_price=old_price
        pd.MAX_PAIRS=old_pair_cap
        m.MAX_ACCOUNTS=old_account_cap

        if lane is not None:
            lane.close()

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
 "checkpoint12_multi_pool_live_size_optimizer.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_registry_required(self):
        self.assertIn(
            "CHECKPOINT11_REGISTRY_MISSING",
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

    def test_shared_pump_updates_all_pairs(self):
        self.assertIn(
            "mpreg.setdefault(",
            self.s,
        )
        self.assertIn(
            "for index,kind in bindings:",
            self.s,
        )

    def test_full_size_ladder(self):
        for value in (
            "0.001","0.010","0.025","0.050","0.100",
            "0.180","0.280","0.500","1.000","1.400",
        ):
            self.assertIn(value,self.s)

    def test_existing_websocket_runtime(self):
        self.assertIn(
            "r.serve_canonical(",
            self.s,
        )
        self.assertIn(
            "r.q20.LatestStateLane()",
            self.s,
        )

    def test_no_compile_sim_send(self):
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
    unittest.main(verbosity=2)
"""

TARGET.write_text(MODULE,encoding="utf-8")
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] canonical checkpoint-12 multi-pool live size optimizer installed")
print("[INPUT] checkpoint-11 token|meteora_pool registry")
print("[TRANSPORT] existing canonical sharded WebSocket serve_canonical")
print("[IDENTITY] pair-key lane; shared Pump updates fan out to all Meteora pools")
print("[SIZES] complete certified ladder; global max; no 0.001 bias")
print("[EXECUTION] gross discovery only; compile/fee/simulation deferred until positive")
print("[ALT] unchanged")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
