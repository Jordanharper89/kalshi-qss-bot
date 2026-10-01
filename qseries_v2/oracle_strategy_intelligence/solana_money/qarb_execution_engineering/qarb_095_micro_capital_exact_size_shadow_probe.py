from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_092_just_in_time_execution_revalidation_gate as q92
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_094_execution_shadow_stability_certification as q94


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_095_micro_capital_exact_size_shadow_probe.json"
)

MICRO_BINDINGS=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_095_micro_capital_shadow_bindings.json"
)

MICRO_TEST_SOL=0.001
MICRO_TEST_LAMPORTS=1_000_000

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


def _load(path):
    p=Path(path)

    if not p.is_file():
        raise RuntimeError(
            "SOURCE_MISSING:"+str(p)
        )

    return json.loads(
        p.read_text(
            encoding="utf-8"
        )
    )


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


def load_certified(root):
    d=_load(
        Path(root)/q94.CERTIFIED
    )

    if d.get("status")!="PASS":
        raise RuntimeError(
            "QARB_094_NOT_PASS"
        )

    rows=d.get("rows") or []

    if not rows:
        raise RuntimeError(
            "QARB_094_NO_CERTIFIED_ROWS"
        )

    return rows


def micro_copy(row):
    # Preserve the production learned size separately.
    # The micro size never overwrites row["size_sol"] upstream.
    return {
        "token":
            row["token"],

        "pump_pool":
            row["pump_pool"],

        "meteora_meta":
            row["meteora_meta"],

        "production_size_sol":
            float(
                row["size_sol"]
            ),

        "size_sol":
            MICRO_TEST_SOL,

        "candidate":
            row.get(
                "candidate"
            ),

        "production_transaction_bytes":
            row.get(
                "transaction_bytes"
            ),

        "stability":
            row.get(
                "stability"
            ),

        "micro_test_only":
            True,
    }


def hydration_bindings(rows):
    return [
        {
            "token":
                x["token"],

            "pump_pool":
                x["pump_pool"],

            "meteora_meta":
                x["meteora_meta"],

            "size_sol":
                MICRO_TEST_SOL,
        }
        for x in rows
    ]


def compile_preferred(
    user,
    route,
    preferred_name
):
    bh=c.rpc(
        "getLatestBlockhash",
        [{
            "commitment":
                "processed"
        }]
    )[
        "value"
    ][
        "blockhash"
    ]

    try:
        extra_alts=(
            q87.las.q59.recent_mriya_alt_keys()
        )
    except Exception:
        extra_alts=[]

    options=q87.alt_sets(
        route["base_alts"],
        extra_alts
    )

    candidates=list(
        q87.repaired_candidates(
            route
        )
    )

    ordered=[]

    if preferred_name:
        for x in candidates:
            if x.get("name")==preferred_name:
                ordered.append(x)
                break

    for x in candidates:
        if x not in ordered:
            ordered.append(x)

    attempts=[]

    for candidate in ordered:
        row=q87.simulate_candidate(
            user,
            None,
            route,
            candidate,
            options,
            bh
        )

        row["diagnostic"]=(
            q87.diagnostic(row)
        )

        attempts.append(row)

        if (
            row.get("compiled")
            and "sim_err" in row
            and row.get("sim_err") is None
            and int(
                row.get(
                    "bytes",
                    q92.MAX_TX_BYTES+1
                )
            )<=q92.MAX_TX_BYTES
        ):
            return {
                "ok":True,

                "selected_candidate":
                    row["name"],

                "selected_bytes":
                    int(
                        row["bytes"]
                    ),

                "sim_err":
                    row.get(
                        "sim_err"
                    ),

                "sim_units":
                    row.get(
                        "sim_units"
                    ),

                "attempts":
                    attempts,
            }

    return {
        "ok":False,
        "reason":
            "NO_CLEAN_UNSIGNED_SIMULATION",
        "attempts":
            attempts,
    }


def run(root=None):
    root=Path(
        root or Path.cwd()
    )

    print(
        "[QARB-095] MICRO-CAPITAL "
        "EXACT-SIZE SHADOW PROBE",
        flush=True
    )

    print(
        "[MICRO] exact_size=0.001000_SOL "
        "lamports=1000000",
        flush=True
    )

    print(
        "[PRESERVE] certified production sizes "
        "remain unchanged",
        flush=True
    )

    print(
        "[RULE] micro result cannot promote, "
        "demote, resize, or mutate production lane",
        flush=True
    )

    certified=load_certified(
        root
    )

    rows=[
        micro_copy(x)
        for x in certified
    ]

    bindings=hydration_bindings(
        rows
    )

    try:
        pairs,_=q87.q86.hydrate(
            root,
            bindings
        )

    except Exception as exc:
        print(
            "[QARB-095 HOLD] "
            "HYDRATION_ERROR:%s:%s"%(
                type(exc).__name__,
                exc
            ),
            flush=True
        )

        return 2

    pair_map={
        p.token:p
        for p in pairs
    }

    _,user=c.sim_identity()

    results={}
    viable=[]

    for row in rows:
        token=row["token"]

        result={
            "token":
                token,

            "production_size_sol":
                row[
                    "production_size_sol"
                ],

            "micro_size_sol":
                MICRO_TEST_SOL,

            "micro_lamports":
                MICRO_TEST_LAMPORTS,

            "pump_pool":
                row["pump_pool"],

            "meteora_pool":
                row[
                    "meteora_meta"
                ][
                    "address"
                ],

            "production_candidate":
                row.get(
                    "candidate"
                ),
        }

        results[token]=result

        pair=pair_map.get(
            token
        )

        if pair is None:
            result[
                "status"
            ]="PAIR_MISSING"

            print(
                "[MICRO_REJECT] "
                "token=%s reason=PAIR_MISSING"%(
                    token[:10]
                ),
                flush=True
            )

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
            ]="MICRO_ROUTE_REJECTED"

            print(
                "[MICRO_REJECT] "
                "token=%s size=0.001000 "
                "reason=%s"%(
                    token[:10],
                    fresh["reason"],
                ),
                flush=True
            )

            continue

        sim=compile_preferred(
            user,
            fresh["route"],
            row.get(
                "candidate"
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
            ]="MICRO_SIM_REJECTED"

            print(
                "[MICRO_REJECT] "
                "token=%s size=0.001000 "
                "reason=%s"%(
                    token[:10],
                    sim.get(
                        "reason"
                    ),
                ),
                flush=True
            )

            continue

        result[
            "status"
        ]="MICRO_SHADOW_PASS"

        result[
            "fresh_net_lamports"
        ]=int(
            fresh[
                "current_net_lamports"
            ]
        )

        result[
            "fresh_net_bps"
        ]=float(
            fresh[
                "current_bps"
            ]
        )

        result[
            "selected_candidate"
        ]=sim[
            "selected_candidate"
        ]

        result[
            "transaction_bytes"
        ]=int(
            sim[
                "selected_bytes"
            ]
        )

        viable.append({
            "token":
                token,

            "production_size_sol":
                row[
                    "production_size_sol"
                ],

            "micro_size_sol":
                MICRO_TEST_SOL,

            "micro_lamports":
                MICRO_TEST_LAMPORTS,

            "pump_pool":
                row["pump_pool"],

            "meteora_meta":
                row["meteora_meta"],

            "fresh_net_lamports":
                result[
                    "fresh_net_lamports"
                ],

            "fresh_net_bps":
                result[
                    "fresh_net_bps"
                ],

            "candidate":
                result[
                    "selected_candidate"
                ],

            "transaction_bytes":
                result[
                    "transaction_bytes"
                ],

            "micro_test_only":
                True,

            "execution_authority":
                False,

            "paper_only":
                True,
        })

        print(
            "[MICRO_SHADOW_PASS] "
            "token=%s "
            "micro=0.001000_SOL "
            "production=%.6f_SOL "
            "net=%+.9f_SOL "
            "bps=%+.2f "
            "candidate=%s "
            "bytes=%d"%(
                token[:10],

                row[
                    "production_size_sol"
                ],

                result[
                    "fresh_net_lamports"
                ]/1e9,

                result[
                    "fresh_net_bps"
                ],

                result[
                    "selected_candidate"
                ],

                result[
                    "transaction_bytes"
                ],
            ),
            flush=True
        )

    status=(
        "PASS"
        if viable
        else "HOLD"
    )

    micro_payload={
        "revision":
            "QARB_095",

        "status":
            status,

        "micro_test_sol":
            MICRO_TEST_SOL,

        "micro_test_lamports":
            MICRO_TEST_LAMPORTS,

        "rows":
            viable,

        "production_sizes_mutated":
            False,

        "micro_test_only":
            True,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "private_key_required":
            False,

        "created_epoch":
            time.time(),
    }

    report={
        "revision":
            "QARB_095",

        "status":
            status,

        "certified_input":
            len(rows),

        "micro_viable":
            len(viable),

        "micro_rejected":
            len(rows)-len(viable),

        "micro_test_sol":
            MICRO_TEST_SOL,

        "micro_test_lamports":
            MICRO_TEST_LAMPORTS,

        "results":
            results,

        "production_sizes_mutated":
            False,

        "production_size_source":
            "QARB_094",

        "micro_test_only":
            True,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "private_key_required":
            False,

        "created_epoch":
            time.time(),
    }

    _save(
        root/MICRO_BINDINGS,
        micro_payload
    )

    _save(
        root/STATE,
        report
    )

    print(
        "[QARB-095] status=%s "
        "certified_input=%d "
        "micro_viable=%d "
        "micro_rejected=%d"%(
            status,
            len(rows),
            len(viable),
            len(rows)-len(viable),
        ),
        flush=True
    )

    print(
        "[PRESERVE] production_sizes_mutated=FALSE",
        flush=True
    )

    print(
        "[MODE] micro_shadow_only "
        "exact_cap=0.001_SOL "
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


def main():
    return run(
        Path.cwd()
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
