from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_093_continuous_execution_shadow_refresh as q93


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_094_execution_shadow_stability_certification.json"
)

CERTIFIED=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_094_certified_execution_shadow_set.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

MIN_CYCLES=3
MIN_PASS_RATE=1.0


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


def load_history(root):
    p=Path(root)/q93.HISTORY

    if not p.is_file():
        raise RuntimeError(
            "QARB_093_HISTORY_MISSING"
        )

    rows=[]

    with p.open(
        "r",
        encoding="utf-8"
    ) as f:
        for line in f:
            line=line.strip()

            if not line:
                continue

            rows.append(
                json.loads(line)
            )

    if not rows:
        raise RuntimeError(
            "QARB_093_HISTORY_EMPTY"
        )

    rows.sort(
        key=lambda x:
            int(
                x.get(
                    "cycle",
                    0
                )
            )
    )

    return rows


def token_universe(history):
    out=set()

    for cycle in history:
        out.update(
            (
                cycle.get(
                    "results"
                )
                or {}
            ).keys()
        )

    return sorted(out)


def observation_for(
    cycle,
    token
):
    result=(
        cycle.get(
            "results"
        )
        or {}
    ).get(
        token
    )

    if not isinstance(
        result,
        dict
    ):
        return {
            "active":False,
            "reason":"NO_RESULT",
        }

    active=(
        result.get(
            "status"
        )
        =="CURRENT_EXECUTION_SHADOW_PASS"
    )

    if not active:
        rv=result.get(
            "revalidation"
        ) or {}

        return {
            "active":False,
            "reason":(
                rv.get(
                    "reason"
                )
                or result.get(
                    "status"
                )
                or "INACTIVE"
            ),
        }

    a=result.get(
        "active"
    ) or {}

    sim=result.get(
        "simulation"
    ) or {}

    return {
        "active":True,

        "bps":
            float(
                a[
                    "fresh_net_bps"
                ]
            ),

        "net_lamports":
            int(
                a[
                    "fresh_net_lamports"
                ]
            ),

        "candidate":
            a.get(
                "candidate"
            ),

        "transaction_bytes":
            int(
                a[
                    "transaction_bytes"
                ]
            ),

        "size_sol":
            float(
                a[
                    "size_sol"
                ]
            ),

        "sim_err":
            a.get(
                "sim_err"
            ),

        "preferred_reused":
            bool(
                sim.get(
                    "preferred_reused",
                    False
                )
            ),

        "pump_pool":
            a.get(
                "pump_pool"
            ),

        "meteora_meta":
            a.get(
                "meteora_meta"
            ),
    }


def transitions(
    observations
):
    drops=0
    reentries=0
    streak=0
    max_streak=0
    prior=None

    for x in observations:
        active=bool(
            x.get(
                "active"
            )
        )

        if active:
            streak+=1
            max_streak=max(
                max_streak,
                streak
            )

        else:
            streak=0

        if prior is True and not active:
            drops+=1

        if prior is False and active:
            reentries+=1

        prior=active

    return {
        "drop_count":drops,
        "reentry_count":reentries,
        "ending_pass_streak":streak,
        "max_pass_streak":max_streak,
    }


def analyze_token(
    token,
    history
):
    observations=[
        observation_for(
            cycle,
            token
        )
        for cycle in history
    ]

    active=[
        x
        for x in observations
        if x.get(
            "active"
        )
    ]

    passes=len(active)
    total=len(
        observations
    )

    pass_rate=(
        passes/total
        if total
        else 0.0
    )

    bps=[
        x["bps"]
        for x in active
    ]

    sizes=[
        x["size_sol"]
        for x in active
    ]

    tx_bytes=[
        x[
            "transaction_bytes"
        ]
        for x in active
    ]

    candidates=[
        x.get(
            "candidate"
        )
        for x in active
        if x.get(
            "candidate"
        )
    ]

    sim_errors=[
        x.get(
            "sim_err"
        )
        for x in active
        if x.get(
            "sim_err"
        ) is not None
    ]

    reused=[
        bool(
            x.get(
                "preferred_reused"
            )
        )
        for x in active
    ]

    tr=transitions(
        observations
    )

    candidate_values=sorted(
        set(candidates)
    )

    byte_values=sorted(
        set(tx_bytes)
    )

    size_values=sorted(
        set(sizes)
    )

    reasons={}

    for x in observations:
        if x.get(
            "active"
        ):
            continue

        reason=str(
            x.get(
                "reason",
                "INACTIVE"
            )
        )

        reasons[reason]=(
            reasons.get(
                reason,
                0
            )
            +1
        )

    certified=bool(
        total>=MIN_CYCLES
        and passes==total
        and pass_rate>=MIN_PASS_RATE
        and bps
        and min(bps)>0
        and not sim_errors
        and len(
            candidate_values
        )==1
        and len(
            byte_values
        )==1
        and len(
            size_values
        )==1
    )

    return {
        "token":
            token,

        "cycles_observed":
            total,

        "passes":
            passes,

        "pass_rate":
            pass_rate,

        "drop_count":
            tr[
                "drop_count"
            ],

        "reentry_count":
            tr[
                "reentry_count"
            ],

        "ending_pass_streak":
            tr[
                "ending_pass_streak"
            ],

        "max_pass_streak":
            tr[
                "max_pass_streak"
            ],

        "bps_min":(
            min(bps)
            if bps
            else None
        ),

        "bps_max":(
            max(bps)
            if bps
            else None
        ),

        "bps_mean":(
            statistics.fmean(
                bps
            )
            if bps
            else None
        ),

        "bps_median":(
            statistics.median(
                bps
            )
            if bps
            else None
        ),

        "bps_population_std":(
            statistics.pstdev(
                bps
            )
            if len(bps)>1
            else 0.0
            if bps
            else None
        ),

        "candidate_values":
            candidate_values,

        "candidate_stable":
            len(
                candidate_values
            )==1
            if active
            else False,

        "transaction_byte_values":
            byte_values,

        "transaction_size_stable":
            len(
                byte_values
            )==1
            if active
            else False,

        "size_values":
            size_values,

        "trade_size_stable":
            len(
                size_values
            )==1
            if active
            else False,

        "preferred_reuse_passes":
            sum(
                1
                for x in reused
                if x
            ),

        "preferred_reuse_rate":(
            sum(
                1
                for x in reused
                if x
            )/len(reused)
            if reused
            else 0.0
        ),

        "sim_error_count":
            len(
                sim_errors
            ),

        "inactive_reasons":
            reasons,

        "certified_stable_shadow":
            certified,
    }


def certified_row(
    analysis,
    current_map
):
    token=analysis[
        "token"
    ]

    current=current_map.get(
        token
    )

    if not isinstance(
        current,
        dict
    ):
        return None

    return {
        "token":
            token,

        "pump_pool":
            current.get(
                "pump_pool"
            ),

        "meteora_meta":
            current.get(
                "meteora_meta"
            ),

        "size_sol":
            current.get(
                "size_sol"
            ),

        "candidate":
            current.get(
                "candidate"
            ),

        "transaction_bytes":
            current.get(
                "transaction_bytes"
            ),

        "stability":{
            "cycles":
                analysis[
                    "cycles_observed"
                ],

            "pass_rate":
                analysis[
                    "pass_rate"
                ],

            "pass_streak":
                analysis[
                    "ending_pass_streak"
                ],

            "bps_min":
                analysis[
                    "bps_min"
                ],

            "bps_mean":
                analysis[
                    "bps_mean"
                ],

            "bps_max":
                analysis[
                    "bps_max"
                ],

            "bps_population_std":
                analysis[
                    "bps_population_std"
                ],

            "preferred_reuse_rate":
                analysis[
                    "preferred_reuse_rate"
                ],
        },

        "execution_authority":
            False,

        "paper_only":
            True,
    }


def run(root=None):
    root=Path(
        root or Path.cwd()
    )

    print(
        "[QARB-094] EXECUTION-SHADOW "
        "STABILITY CERTIFICATION",
        flush=True
    )

    print(
        "[SOURCE] frozen QARB-093 "
        "JSONL history only",
        flush=True
    )

    print(
        "[MEASURE] pass streak, drops, "
        "reentries, bps distribution, "
        "candidate/tx-size stability",
        flush=True
    )

    history=load_history(
        root
    )

    current_path=(
        root/q93.CURRENT
    )

    current={}

    if current_path.is_file():
        d=json.loads(
            current_path.read_text(
                encoding="utf-8"
            )
        )

        current={
            x["token"]:x
            for x in d.get(
                "rows",
                []
            )
            if x.get(
                "token"
            )
        }

    analyses=[]

    for token in token_universe(
        history
    ):
        analyses.append(
            analyze_token(
                token,
                history
            )
        )

    certified=[
        x
        for x in analyses
        if x[
            "certified_stable_shadow"
        ]
    ]

    certified_rows=[]

    for x in certified:
        row=certified_row(
            x,
            current
        )

        if row is not None:
            certified_rows.append(
                row
            )

    certified_rows.sort(
        key=lambda x:
            (
                x[
                    "stability"
                ][
                    "bps_mean"
                ]
                or 0.0
            ),
        reverse=True
    )

    status=(
        "PASS"
        if certified_rows
        else "HOLD"
    )

    report={
        "revision":
            "QARB_094",

        "status":
            status,

        "history_cycles":
            len(history),

        "tokens_observed":
            len(analyses),

        "certified_count":
            len(
                certified_rows
            ),

        "certified_tokens":[
            x["token"]
            for x in certified_rows
        ],

        "analysis":
            analyses,

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

    payload={
        "revision":
            "QARB_094",

        "status":
            status,

        "rows":
            certified_rows,

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
        root/STATE,
        report
    )

    _save(
        root/CERTIFIED,
        payload
    )

    for x in analyses:
        print(
            "[2S_STABILITY] "
            "token=%s "
            "cycles=%d passes=%d "
            "pass_rate=%.1f%% "
            "streak=%d drops=%d "
            "reentries=%d "
            "bps_min=%s "
            "bps_mean=%s "
            "bps_max=%s "
            "tx_stable=%s "
            "candidate_stable=%s "
            "reuse=%.1f%% "
            "certified=%s"%(
                x[
                    "token"
                ][:10],

                x[
                    "cycles_observed"
                ],

                x[
                    "passes"
                ],

                x[
                    "pass_rate"
                ]*100.0,

                x[
                    "ending_pass_streak"
                ],

                x[
                    "drop_count"
                ],

                x[
                    "reentry_count"
                ],

                (
                    "%.2f"
                    %x[
                        "bps_min"
                    ]
                    if x[
                        "bps_min"
                    ] is not None
                    else "NA"
                ),

                (
                    "%.2f"
                    %x[
                        "bps_mean"
                    ]
                    if x[
                        "bps_mean"
                    ] is not None
                    else "NA"
                ),

                (
                    "%.2f"
                    %x[
                        "bps_max"
                    ]
                    if x[
                        "bps_max"
                    ] is not None
                    else "NA"
                ),

                x[
                    "transaction_size_stable"
                ],

                x[
                    "candidate_stable"
                ],

                x[
                    "preferred_reuse_rate"
                ]*100.0,

                x[
                    "certified_stable_shadow"
                ],
            ),
            flush=True
        )

    print(
        "[QARB-094] status=%s "
        "history_cycles=%d "
        "tokens=%d certified=%d"%(
            status,
            len(history),
            len(analyses),
            len(certified_rows),
        ),
        flush=True
    )

    print(
        "[CERTIFIED] %s"%(
            root/CERTIFIED
        ),
        flush=True
    )

    print(
        "[MODE] evidence_certification_only "
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
