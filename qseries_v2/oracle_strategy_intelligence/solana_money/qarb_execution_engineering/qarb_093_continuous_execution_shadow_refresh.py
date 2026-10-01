from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_091_current_execution_simulation_envelope as q91
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_092_just_in_time_execution_revalidation_gate as q92


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_093_continuous_execution_shadow_refresh.json"
)

CURRENT=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_093_current_execution_shadow_bindings.json"
)

HISTORY=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_093_execution_shadow_history.jsonl"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

DEFAULT_SECONDS=120.0
DEFAULT_REFRESH_SECONDS=30.0
MIN_REFRESH_SECONDS=20.0


def _save(path,payload):
    p=Path(path)
    p.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tmp=p.with_suffix(
        p.suffix+".tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )

    tmp.replace(p)


def _append(path,payload):
    p=Path(path)

    p.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with p.open(
        "a",
        encoding="utf-8"
    ) as f:
        f.write(
            json.dumps(
                payload,
                sort_keys=True
            )
            +"\n"
        )


def load_prior_candidates(root):
    p=Path(root)/q92.BINDINGS

    if not p.is_file():
        return {}

    try:
        d=json.loads(
            p.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return {}

    out={}

    for row in d.get(
        "rows",
        []
    ):
        token=row.get(
            "token"
        )

        candidate=row.get(
            "candidate"
        )

        if token and candidate:
            out[token]=candidate

    return out


def clean_sim(row):
    return bool(
        row.get("compiled")
        and "sim_err" in row
        and row.get("sim_err") is None
        and int(
            row.get(
                "bytes",
                q92.MAX_TX_BYTES+1
            )
        )<=q92.MAX_TX_BYTES
    )


def preferred_simulation(
    user,
    route,
    extra_alts,
    preferred_name=None
):
    bh=c.rpc(
        "getLatestBlockhash",
        [{
            "commitment":"processed"
        }]
    )[
        "value"
    ][
        "blockhash"
    ]

    options=q87.alt_sets(
        route["base_alts"],
        extra_alts
    )

    candidates=list(
        q87.repaired_candidates(
            route
        )
    )

    if preferred_name:
        preferred=next(
            (
                x
                for x in candidates
                if x.get(
                    "name"
                )==preferred_name
            ),
            None
        )

        if preferred is not None:
            x=q87.simulate_candidate(
                user,
                None,
                route,
                preferred,
                options,
                bh
            )

            x["diagnostic"]=(
                q87.diagnostic(x)
            )

            if clean_sim(x):
                return {
                    "ok":True,
                    "reason":
                        "PREFERRED_UNSIGNED_SIMULATION_PASS",
                    "selected_candidate":
                        x["name"],
                    "selected_bytes":
                        int(
                            x["bytes"]
                        ),
                    "selected_alt_count":
                        int(
                            x.get(
                                "alt_count",
                                0
                            )
                        ),
                    "sim_err":
                        x.get(
                            "sim_err"
                        ),
                    "sim_units":
                        x.get(
                            "sim_units"
                        ),
                    "attempts":[x],
                    "preferred_reused":
                        True,
                }

    # Exact certified QARB-092 fallback.
    x=q92.compile_and_simulate(
        user,
        route,
        extra_alts
    )

    x["preferred_reused"]=False

    return x


def one_cycle(
    root,
    cycle,
    prior_candidates=None
):
    root=Path(root)

    prior_candidates=(
        prior_candidates
        or {}
    )

    cycle_started=time.time()

    rows=q91.intake_rows(
        root
    )

    valid=[]

    for row in rows:
        ok,_=q91.validate_intake_row(
            row
        )

        if ok:
            valid.append(row)

    bindings=q91.hydration_bindings(
        valid
    )

    # Every cycle creates fresh physical pair state.
    pairs,_=q87.q86.hydrate(
        root,
        bindings
    )

    pair_map={
        p.token:p
        for p in pairs
    }

    _,user=c.sim_identity()

    try:
        extra_alts=(
            q87.las.q59.recent_mriya_alt_keys()
        )

    except Exception:
        extra_alts=[]

    active=[]
    rejects=[]
    results={}

    for row in valid:
        token=row["token"]

        result={
            "token":
                token,

            "size_sol":
                float(
                    row["size_sol"]
                ),

            "pump_pool":
                row["pump_pool"],

            "meteora_pool":
                row[
                    "meteora_meta"
                ][
                    "address"
                ],

            "cycle":
                cycle,
        }

        results[token]=result

        pair=pair_map.get(
            token
        )

        if pair is None:
            result[
                "status"
            ]="PAIR_MISSING"

            rejects.append({
                "token":token,
                "reason":"PAIR_MISSING",
            })

            continue

        fresh=q92.revalidate_route(
            user,
            pair,
            row
        )

        result[
            "revalidation"
        ]={
            k:v
            for k,v in fresh.items()
            if k!="route"
        }

        if not fresh["ok"]:
            result[
                "status"
            ]="CURRENTLY_INACTIVE"

            rejects.append({
                "token":token,
                "reason":
                    fresh["reason"],
            })

            print(
                "[2S_SHADOW_DROP] "
                "cycle=%d token=%s "
                "reason=%s"%(
                    cycle,
                    token[:10],
                    fresh["reason"],
                ),
                flush=True
            )

            continue

        sim=preferred_simulation(
            user,
            fresh["route"],
            extra_alts,
            prior_candidates.get(
                token
            )
        )

        result[
            "simulation"
        ]=sim

        if not sim.get(
            "ok"
        ):
            result[
                "status"
            ]="CURRENTLY_INACTIVE"

            rejects.append({
                "token":token,
                "reason":
                    sim.get(
                        "reason",
                        "SIMULATION_REJECT"
                    ),
            })

            print(
                "[2S_SHADOW_DROP] "
                "cycle=%d token=%s "
                "reason=%s"%(
                    cycle,
                    token[:10],
                    sim.get(
                        "reason"
                    ),
                ),
                flush=True
            )

            continue

        current={
            "token":
                token,

            "pump_pool":
                row["pump_pool"],

            "meteora_meta":
                row["meteora_meta"],

            "size_sol":
                float(
                    row["size_sol"]
                ),

            "fresh_net_lamports":
                int(
                    fresh[
                        "current_net_lamports"
                    ]
                ),

            "fresh_net_bps":
                float(
                    fresh[
                        "current_bps"
                    ]
                ),

            "candidate":
                sim[
                    "selected_candidate"
                ],

            "transaction_bytes":
                int(
                    sim[
                        "selected_bytes"
                    ]
                ),

            "sim_err":
                sim.get(
                    "sim_err"
                ),

            "cycle":
                cycle,

            "observed_epoch":
                time.time(),

            "execution_authority":
                False,

            "paper_only":
                True,
        }

        active.append(
            current
        )

        result[
            "status"
        ]="CURRENT_EXECUTION_SHADOW_PASS"

        result[
            "active"
        ]=current

        print(
            "[2S_SHADOW_ACTIVE] "
            "cycle=%d token=%s "
            "size=%.6f bps=%+.2f "
            "candidate=%s bytes=%d "
            "preferred_reused=%s"%(
                cycle,
                token[:10],
                current[
                    "size_sol"
                ],
                current[
                    "fresh_net_bps"
                ],
                current[
                    "candidate"
                ],
                current[
                    "transaction_bytes"
                ],
                str(
                    sim.get(
                        "preferred_reused",
                        False
                    )
                ),
            ),
            flush=True
        )

    cycle_result={
        "cycle":
            cycle,

        "started_epoch":
            cycle_started,

        "completed_epoch":
            time.time(),

        "input_rows":
            len(rows),

        "validated_rows":
            len(valid),

        "active_count":
            len(active),

        "rejected_count":
            len(rejects),

        "active_tokens":[
            x["token"]
            for x in active
        ],

        "rejections":
            rejects,

        "results":
            results,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,
    }

    return (
        cycle_result,
        active
    )


def run(
    root=None,
    seconds=DEFAULT_SECONDS,
    refresh_seconds=DEFAULT_REFRESH_SECONDS
):
    root=Path(
        root or Path.cwd()
    )

    seconds=max(
        1.0,
        float(seconds)
    )

    refresh=max(
        MIN_REFRESH_SECONDS,
        float(refresh_seconds)
    )

    print(
        "[QARB-093] CONTINUOUS "
        "EXECUTION-SHADOW REFRESH",
        flush=True
    )

    print(
        "[SOURCE] QARB-090 four-token "
        "candidate set reconsidered every cycle",
        flush=True
    )

    print(
        "[REFRESH] fresh hydration -> "
        "JIT route -> compact tx -> unsigned sim",
        flush=True
    )

    print(
        "[RECYCLE] dropped tokens remain eligible "
        "for later re-entry",
        flush=True
    )

    print(
        "[CADENCE] refresh>=%.1fs"%(
            MIN_REFRESH_SECONDS
        ),
        flush=True
    )

    prior_candidates=(
        load_prior_candidates(
            root
        )
    )

    started=time.monotonic()
    cycle=0
    cycles=[]
    ever_active=set()
    last_active=[]

    while True:
        elapsed=(
            time.monotonic()
            -started
        )

        if (
            cycle>0
            and elapsed>=seconds
        ):
            break

        cycle+=1

        try:
            result,active=one_cycle(
                root,
                cycle,
                prior_candidates
            )

        except Exception as exc:
            result={
                "cycle":cycle,
                "started_epoch":
                    time.time(),
                "completed_epoch":
                    time.time(),
                "status":
                    "CYCLE_EXCEPTION",
                "error":
                    type(exc).__name__
                    +":"
                    +str(exc),
                "active_count":0,
                "execution_authority":
                    False,
                "paper_only":
                    True,
                "real_money_moved":
                    False,
            }

            active=[]

            print(
                "[SHADOW_CYCLE_HOLD] "
                "cycle=%d %s:%s"%(
                    cycle,
                    type(exc).__name__,
                    exc
                ),
                flush=True
            )

        cycles.append(
            result
        )

        _append(
            root/HISTORY,
            result
        )

        last_active=active

        for x in active:
            token=x["token"]

            if (
                token not in ever_active
                and cycle>1
            ):
                print(
                    "[2S_SHADOW_REENTRY] "
                    "cycle=%d token=%s"%(
                        cycle,
                        token[:10]
                    ),
                    flush=True
                )

            ever_active.add(
                token
            )

            prior_candidates[
                token
            ]=x[
                "candidate"
            ]

        current_payload={
            "revision":
                "QARB_093",

            "status":(
                "PASS"
                if active
                else "HOLD_NO_CURRENT_ACTIVE"
            ),

            "cycle":
                cycle,

            "rows":
                active,

            "execution_authority":
                False,

            "paper_only":
                True,

            "real_money_moved":
                False,

            "private_key_required":
                False,

            "updated_epoch":
                time.time(),
        }

        _save(
            root/CURRENT,
            current_payload
        )

        print(
            "[SHADOW_CYCLE] "
            "cycle=%d active=%d "
            "rejected=%d"%(
                cycle,
                len(active),
                int(
                    result.get(
                        "rejected_count",
                        0
                    )
                ),
            ),
            flush=True
        )

        remain=(
            seconds
            -(
                time.monotonic()
                -started
            )
        )

        if remain<=0:
            break

        time.sleep(
            min(
                refresh,
                remain
            )
        )

    successful_cycles=[
        x
        for x in cycles
        if int(
            x.get(
                "active_count",
                0
            )
        )>0
    ]

    status=(
        "PASS"
        if successful_cycles
        else "HOLD"
    )

    report={
        "revision":
            "QARB_093",

        "status":
            status,

        "cycles":
            len(cycles),

        "successful_cycles":
            len(successful_cycles),

        "ever_active_tokens":
            sorted(
                ever_active
            ),

        "ever_active_count":
            len(ever_active),

        "final_active_tokens":[
            x["token"]
            for x in last_active
        ],

        "final_active_count":
            len(last_active),

        "refresh_seconds":
            refresh,

        "requested_seconds":
            seconds,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "private_key_required":
            False,

        "completed_epoch":
            time.time(),
    }

    _save(
        root/STATE,
        report
    )

    print(
        "[QARB-093] status=%s "
        "cycles=%d successful=%d "
        "ever_active=%d final_active=%d"%(
            status,
            len(cycles),
            len(successful_cycles),
            len(ever_active),
            len(last_active),
        ),
        flush=True
    )

    print(
        "[CURRENT] %s"%(
            root/CURRENT
        ),
        flush=True
    )

    print(
        "[HISTORY] %s"%(
            root/HISTORY
        ),
        flush=True
    )

    print(
        "[MODE] continuous_unsigned_shadow "
        "private_key_required=FALSE "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    return (
        0
        if status=="PASS"
        else 2
    )


def main(argv=None):
    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=DEFAULT_SECONDS
    )

    ap.add_argument(
        "--refresh-seconds",
        type=float,
        default=DEFAULT_REFRESH_SECONDS
    )

    a=ap.parse_args(
        argv
    )

    return run(
        Path.cwd(),
        a.seconds,
        a.refresh_seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
