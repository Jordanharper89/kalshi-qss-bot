from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_086_two_second_dynamic_execution_binding_cutover as q86
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_089_two_second_dlmm_liquidity_binding_recovery as q89


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_090_current_executable_liquidity_intake_gate.json"
)

BINDINGS=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_090_current_executable_liquidity_bindings.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


def _load(path,default=None):
    p=Path(path)

    if not p.is_file():
        return default

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


def physical_row_ok(row):
    if not isinstance(
        row,
        dict
    ):
        return False

    selected=row.get(
        "selected_binding"
    )

    if not isinstance(
        selected,
        dict
    ):
        return False

    if selected.get(
        "recovered_from_remembered"
    ):
        # 089 currently records alternate address only.
        # Do not invent replacement pool metadata.
        return False

    try:
        net=int(
            selected[
                "net_lamports"
            ]
        )

        bps=float(
            selected[
                "net_bps"
            ]
        )

    except Exception:
        return False

    return (
        net>0
        and bps>0
    )


def select_bindings(
    memory_bindings,
    report
):
    results=(
        report.get(
            "results",
            {}
        )
        if isinstance(
            report,
            dict
        )
        else {}
    )

    selected=[]
    rejected=[]

    for binding in memory_bindings:
        token=binding.get(
            "token"
        )

        row=results.get(
            token,
            {}
        )

        if physical_row_ok(
            row
        ):
            evidence=row[
                "selected_binding"
            ]

            selected.append({
                **binding,

                "qarb_090_physical_liquidity":{
                    "net_lamports":
                        int(
                            evidence[
                                "net_lamports"
                            ]
                        ),

                    "net_bps":
                        float(
                            evidence[
                                "net_bps"
                            ]
                        ),

                    "size_sol":
                        float(
                            evidence[
                                "size_sol"
                            ]
                        ),

                    "meteora_pool":
                        evidence[
                            "meteora_pool"
                        ],

                    "source":
                        "QARB_089",
                },
            })

        else:
            reason="NO_COMPLETE_POSITIVE_ROUTE"

            if isinstance(
                row,
                dict
            ):
                sb=row.get(
                    "selected_binding"
                )

                if isinstance(
                    sb,
                    dict
                ):
                    if sb.get(
                        "recovered_from_remembered"
                    ):
                        reason=(
                            "ALTERNATE_POOL_METADATA_"
                            "NOT_CUTOVER_CERTIFIED"
                        )

                    else:
                        try:
                            if int(
                                sb.get(
                                    "net_lamports",
                                    0
                                )
                            )<=0:
                                reason=(
                                    "CURRENT_ROUTE_"
                                    "NONPOSITIVE"
                                )
                        except Exception:
                            pass

            rejected.append({
                "token":token,
                "reason":reason,
                "qarb_089_status":
                    row.get(
                        "status"
                    )
                    if isinstance(
                        row,
                        dict
                    )
                    else None,
            })

    selected.sort(
        key=lambda x:
            x[
                "qarb_090_physical_liquidity"
            ][
                "net_bps"
            ],
        reverse=True
    )

    return (
        selected,
        rejected
    )


def run(root=None):
    root=Path(
        root or Path.cwd()
    )

    print(
        "[QARB-090] CURRENT EXECUTABLE "
        "LIQUIDITY INTAKE GATE",
        flush=True
    )

    print(
        "[SOURCE] frozen QARB-080 memory "
        "+ physical QARB-089 liquidity evidence",
        flush=True
    )

    memory,audit=(
        q86.memory_candidates(
            root
        )
    )

    report=_load(
        root/q89.STATE
    )

    if not isinstance(
        report,
        dict
    ):
        print(
            "[QARB-090 HOLD] "
            "QARB-089 physical report missing",
            flush=True
        )
        return 2

    if report.get(
        "status"
    )!="PASS":
        print(
            "[QARB-090 HOLD] "
            "QARB-089 not PASS",
            flush=True
        )
        return 2

    selected,rejected=(
        select_bindings(
            memory,
            report
        )
    )

    rows=[]

    for x in selected:
        ev=x[
            "qarb_090_physical_liquidity"
        ]

        rows.append({
            "token":
                x["token"],

            "pump_pool":
                x.get(
                    "pump_pool"
                ),

            "meteora_meta":
                x.get(
                    "meteora_meta"
                ),

            "size_sol":
                ev[
                    "size_sol"
                ],

            "physical_net_lamports":
                ev[
                    "net_lamports"
                ],

            "physical_net_bps":
                ev[
                    "net_bps"
                ],

            "source_binding":
                x,

            "execution_authority":
                False,

            "paper_only":
                True,
        })

    status=(
        "PASS"
        if rows
        else "HOLD"
    )

    binding_payload={
        "revision":
            "QARB_090",

        "status":
            status,

        "rows":
            rows,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "created_unix":
            time.time(),
    }

    report_payload={
        "revision":
            "QARB_090",

        "status":
            status,

        "memory_candidates":
            len(memory),

        "admitted":
            len(rows),

        "rejected":
            len(rejected),

        "admitted_tokens":[
            x[
                "token"
            ]
            for x in rows
        ],

        "rejections":
            rejected,

        "binding_audit":
            audit,

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
        root/BINDINGS,
        binding_payload
    )

    _save(
        root/STATE,
        report_payload
    )

    for row in rows:
        print(
            "[2S_EXEC_INTAKE] "
            "token=%s size=%.6f "
            "net=%+.9f_SOL "
            "bps=%+.2f status=ADMITTED"%(
                row[
                    "token"
                ][:10],

                row[
                    "size_sol"
                ],

                row[
                    "physical_net_lamports"
                ]/1e9,

                row[
                    "physical_net_bps"
                ],
            ),
            flush=True
        )

    for row in rejected:
        print(
            "[2S_EXEC_REJECT] "
            "token=%s reason=%s"%(
                (
                    row.get(
                        "token"
                    )
                    or ""
                )[:10],

                row[
                    "reason"
                ],
            ),
            flush=True
        )

    print(
        "[QARB-090] status=%s "
        "memory=%d admitted=%d "
        "rejected=%d"%(
            status,
            len(memory),
            len(rows),
            len(rejected),
        ),
        flush=True
    )

    print(
        "[BINDINGS] %s"%(
            root/BINDINGS
        ),
        flush=True
    )

    print(
        "[MODE] intake_only "
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
