from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_atomic_simulation as las
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_038b_nonrecursive_mriya_hotset_runtime as hot
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_076_active_execution_binding_materializer as q76


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_085_two_second_executable_envelope.json"
)

TARGET_HORIZON="2"
MIN_2S_SAMPLES=3
MIN_2S_WIN_RATE=0.80
MIN_2S_PNL_SOL=0.0

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


def _save(root,payload):
    p=Path(root)/STATE

    p.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    t=p.with_suffix(
        p.suffix+".tmp"
    )

    t.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )

    t.replace(p)


def _horizon(row,target="2"):
    for k,v in row.get(
        "horizons",
        {}
    ).items():

        try:
            normalized=str(
                int(
                    float(k)
                )
            )
        except Exception:
            normalized=str(k)

        if normalized==target:
            return dict(v)

    return {}


def two_second_evidence(row):
    h=_horizon(
        row,
        TARGET_HORIZON
    )

    n=int(
        h.get(
            "samples",
            0
        )
    )

    wins=int(
        h.get(
            "wins",
            0
        )
    )

    pnl=float(
        h.get(
            "pnl_sol",
            0.0
        )
    )

    wr=(
        wins/n
        if n
        else 0.0
    )

    admitted=(
        n>=MIN_2S_SAMPLES
        and wr>=MIN_2S_WIN_RATE
        and pnl>MIN_2S_PNL_SOL
    )

    reasons=[]

    if n<MIN_2S_SAMPLES:
        reasons.append(
            "INSUFFICIENT_2S_SAMPLES"
        )

    if wr<MIN_2S_WIN_RATE:
        reasons.append(
            "2S_WIN_RATE_BELOW_GATE"
        )

    if pnl<=MIN_2S_PNL_SOL:
        reasons.append(
            "2S_PNL_NOT_POSITIVE"
        )

    return {
        "samples":n,
        "wins":wins,
        "win_rate":wr,
        "pnl_sol":pnl,
        "admitted":admitted,
        "hold_reasons":reasons,
    }


def attempt_reason(row):
    if row.get(
        "profitable"
    ):
        return "PROFITABLE_SIMULATION"

    if not row.get(
        "compiled",
        False
    ):
        return (
            "COMPILE_FAIL:"
            +str(
                row.get(
                    "error"
                )
            )
        )

    if row.get(
        "sim_err"
    ) is not None:
        return (
            "SIM_ERROR:"
            +str(
                row.get(
                    "sim_err"
                )
            )
        )

    pnl=row.get(
        "sim_pnl_lamports"
    )

    if pnl is None:
        return "SIM_PNL_UNAVAILABLE"

    if int(pnl)<=0:
        return "SIM_PNL_NONPOSITIVE"

    bps=row.get(
        "sim_bps"
    )

    if bps is None:
        return "SIM_BPS_UNAVAILABLE"

    if float(bps)<float(
        las.q59.MIN_NET_BPS
    ):
        return "SIM_BPS_BELOW_GATE"

    return "UNCLASSIFIED_REJECT"


def audit(root):
    root=Path(root)

    learned=q70._load(
        root
    ).get(
        "tokens",
        {}
    )

    bindings=q76.materialize(
        root
    )

    pairs,_=hot.priority_prepare_pairs(
        root
    )

    pair_map={
        (
            p.token,
            p.pump_pool,
            p.meteora_pool
        ):p
        for p in pairs
    }

    kp,user=c.sim_identity()

    rows={}
    admitted=0
    composed=0
    profitable=0

    for token,binding in sorted(
        bindings.get(
            "bindings",
            {}
        ).items()
    ):
        evidence=two_second_evidence(
            learned.get(
                token,
                {}
            )
        )

        row={
            "token":token,
            "size_sol":
                float(
                    binding.get(
                        "size_sol",
                        0.0
                    )
                ),
            "pump_pool":
                binding.get(
                    "pump_pool"
                ),
            "meteora_pool":
                binding.get(
                    "meteora_pool"
                ),
            "bound":
                bool(
                    binding.get(
                        "bound"
                    )
                ),
            "two_second":
                evidence,
            "execution_authority":
                False,
            "real_money_moved":
                False,
        }

        rows[token]=row

        if not evidence[
            "admitted"
        ]:
            row["status"]="RESEARCH_ONLY"
            continue

        if not binding.get(
            "bound"
        ):
            row["status"]="NO_CURRENT_BINDING"
            continue

        admitted+=1

        pair=pair_map.get(
            (
                token,
                binding.get(
                    "pump_pool"
                ),
                binding.get(
                    "meteora_pool"
                )
            )
        )

        if pair is None:
            row[
                "status"
            ]="CURRENT_EXACT_PAIR_NOT_FOUND"
            continue

        try:
            route=las.compose_bound(
                user,
                pair,
                float(
                    binding[
                        "size_sol"
                    ]
                )
            )

            composed+=1

            row[
                "pre_sim_net_sol"
            ]=(
                route[
                    "pre_sim_net_lamports"
                ]/1e9
            )

            row[
                "pre_sim_bps"
            ]=route[
                "pre_sim_bps"
            ]

            row[
                "candidate_count"
            ]=len(
                route.get(
                    "candidates",
                    []
                )
            )

            bh=c.rpc(
                "getLatestBlockhash",
                [
                    {
                        "commitment":
                            "processed"
                    }
                ]
            )[
                "value"
            ][
                "blockhash"
            ]

            winner,attempts=(
                las.q59.attempt_candidate_simulations(
                    user,
                    kp,
                    route,
                    bh
                )
            )

            analyzed=[]

            for x in attempts:
                z=dict(x)
                z[
                    "diagnostic"
                ]=attempt_reason(
                    z
                )
                analyzed.append(
                    z
                )

            row[
                "attempts"
            ]=analyzed

            row[
                "winner"
            ]=winner

            row[
                "profitable_simulation"
            ]=bool(
                winner
                and winner.get(
                    "profitable"
                )
            )

            if row[
                "profitable_simulation"
            ]:
                profitable+=1

                row[
                    "status"
                ]="EXECUTABLE_2S_SIM_PASS"

            else:
                row[
                    "status"
                ]="NO_PROFITABLE_SIMULATION"

        except Exception as exc:
            row[
                "status"
            ]="SIMULATION_EXCEPTION"

            row[
                "error"
            ]=(
                type(
                    exc
                ).__name__
                +":"
                +str(
                    exc
                )
            )

    out={
        "revision":
            "QARB_085",

        "target_horizon_seconds":
            2,

        "policy":{
            "min_samples":
                MIN_2S_SAMPLES,
            "min_win_rate":
                MIN_2S_WIN_RATE,
            "min_pnl_sol":
                MIN_2S_PNL_SOL,
            "route":
                "PUMPSWAP_TO_METEORA_DLMM",
        },

        "bound_tokens":
            len(
                bindings.get(
                    "bindings",
                    {}
                )
            ),

        "two_second_admitted":
            admitted,

        "atomic_composed":
            composed,

        "profitable_simulations":
            profitable,

        "rows":
            rows,

        "simulation_only":
            True,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "created_unix":
            time.time(),
    }

    _save(
        root,
        out
    )

    return out


def main():
    r=audit(
        Path.cwd()
    )

    print(
        "[QARB-085] 2-SECOND EXECUTABLE "
        "ENVELOPE DIAGNOSTIC"
    )

    print(
        "[POLICY] 2s samples>=%d "
        "win_rate>=%.0f%% pnl>0"%(
            MIN_2S_SAMPLES,
            MIN_2S_WIN_RATE*100
        )
    )

    print(
        "[COUNTS] bound=%d admitted_2s=%d "
        "composed=%d profitable_sim=%d"%(
            r[
                "bound_tokens"
            ],
            r[
                "two_second_admitted"
            ],
            r[
                "atomic_composed"
            ],
            r[
                "profitable_simulations"
            ]
        )
    )

    for token,x in r[
        "rows"
    ].items():

        h=x[
            "two_second"
        ]

        if not h[
            "admitted"
        ]:
            continue

        print(
            "[2S_CANDIDATE] token=%s "
            "n=%d wr=%.1f%% pnl=%+.9f "
            "size=%.6f status=%s"%(
                token[:10],
                h[
                    "samples"
                ],
                h[
                    "win_rate"
                ]*100.0,
                h[
                    "pnl_sol"
                ],
                x[
                    "size_sol"
                ],
                x.get(
                    "status"
                )
            )
        )

        for a in x.get(
            "attempts",
            []
        ):
            print(
                "[2S_SIM_ATTEMPT] token=%s "
                "candidate=%s bytes=%s "
                "sim_pnl=%s sim_bps=%s "
                "diagnostic=%s"%(
                    token[:10],
                    a.get(
                        "name"
                    ),
                    a.get(
                        "bytes"
                    ),
                    a.get(
                        "sim_pnl_lamports"
                    ),
                    a.get(
                        "sim_bps"
                    ),
                    a.get(
                        "diagnostic"
                    )
                )
            )

    status=(
        "PASS"
        if r[
            "profitable_simulations"
        ]>0
        else "HOLD"
    )

    print(
        "[2S_EXECUTABLE_ENVELOPE] "
        "status=%s profitable=%d"%(
            status,
            r[
                "profitable_simulations"
            ]
        )
    )

    print(
        "[MODE] simulation_only "
        "execution_authority=FALSE "
        "real_money_moved=FALSE"
    )

    return 0


if __name__=="__main__":
    raise SystemExit(
        main()
    )
