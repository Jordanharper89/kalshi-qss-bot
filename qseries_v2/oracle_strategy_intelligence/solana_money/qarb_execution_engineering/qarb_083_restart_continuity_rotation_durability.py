from __future__ import annotations
import json,subprocess,sys,time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_080_single_runtime_dynamic_mriya_supervisor as q80
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_081_proven_arbitrage_lifecycle_certification as q81
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_082_consolidated_one_runtime_cutover as q82

STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_083_restart_continuity_rotation_durability.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


def _load(path,default):
    try:
        return json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return default


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


def snapshot(root):
    root=Path(root)

    learned=q70._load(
        root
    ).get(
        "tokens",
        {}
    )

    seen=set(
        _load(
            root/q80.SEEN,
            {"tokens":[]}
        ).get(
            "tokens",
            []
        )
    )

    memory=set(
        _load(
            root/q80.MEMORY,
            {"rows":{}}
        ).get(
            "rows",
            {}
        )
    )

    cert=q81.certify(
        root
    )

    q80_state=_load(
        root/q80.STATE,
        {}
    )

    q82_state=_load(
        root/q82.STATE,
        {}
    )

    return {
        "tokens":{
            token:{
                "samples":
                    int(
                        x.get(
                            "samples",
                            0
                        )
                    ),
                "wins":
                    int(
                        x.get(
                            "wins",
                            0
                        )
                    ),
                "pnl_sol":
                    float(
                        x.get(
                            "pnl_sol",
                            0.0
                        )
                    ),
            }
            for token,x
            in learned.items()
        },

        "seen":
            sorted(seen),

        "memory":
            sorted(memory),

        "proven_tokens":
            sorted(
                cert.get(
                    "proven_tokens",
                    {}
                )
            ),

        "recyclable_proven_tokens":
            sorted(
                cert.get(
                    "recyclable_proven_tokens",
                    []
                )
            ),

        "restart_continuity":
            dict(
                cert.get(
                    "restart_continuity",
                    {}
                )
            ),

        "q80_state":
            q80_state,

        "q82_state":
            q82_state,
    }


def compare(
    before,
    after,
    child_rc
):
    violations=[]

    bt=before[
        "tokens"
    ]

    at=after[
        "tokens"
    ]

    for token,old in bt.items():
        cur=at.get(
            token
        )

        if cur is None:
            violations.append(
                "TOKEN_HISTORY_LOST:"
                +token
            )
            continue

        if (
            cur["samples"]
            <
            old["samples"]
        ):
            violations.append(
                "SAMPLE_ROLLBACK:"
                +token
            )

        if (
            cur["wins"]
            <
            old["wins"]
        ):
            violations.append(
                "WIN_ROLLBACK:"
                +token
            )

    if not set(
        before["seen"]
    ).issubset(
        set(
            after["seen"]
        )
    ):
        violations.append(
            "SEEN_HISTORY_ROLLBACK"
        )

    if not set(
        before["memory"]
    ).issubset(
        set(
            after["memory"]
        )
    ):
        violations.append(
            "BINDING_MEMORY_ROLLBACK"
        )

    for token in before[
        "proven_tokens"
    ]:
        if token not in at:
            violations.append(
                "PROVEN_HISTORY_LOST:"
                +token
            )

        if token not in set(
            after["memory"]
        ):
            violations.append(
                "PROVEN_BINDING_MEMORY_LOST:"
                +token
            )

    q80s=after.get(
        "q80_state",
        {}
    )

    q82s=after.get(
        "q82_state",
        {}
    )

    if child_rc!=0:
        violations.append(
            "RESTART_CHILD_NONZERO:"
            +str(child_rc)
        )

    if q82s.get(
        "status"
    )!="PASS":
        violations.append(
            "QARB_082_POST_RESTART_NOT_PASS"
        )

    if q82s.get(
        "runtime_return_code"
    ) not in (
        0,
        None
    ):
        violations.append(
            "QARB_082_RUNTIME_NONZERO"
        )

    if q82s.get(
        "single_manual_launcher"
    ) is not True:
        violations.append(
            "ONE_LAUNCHER_CONTRACT_LOST"
        )

    if int(
        q80s.get(
            "generation",
            0
        )
    )<2:
        violations.append(
            "ROTATION_DID_NOT_REACH_TWO_GENERATIONS"
        )

    if int(
        q80s.get(
            "transport_failures",
            0
        )
    )!=0:
        violations.append(
            "TRANSPORT_FAILURE_AFTER_RESTART"
        )

    if not q80s.get(
        "usable_tokens",
        []
    ):
        violations.append(
            "NO_USABLE_TOKENS_AFTER_RESTART"
        )

    continuity=after.get(
        "restart_continuity",
        {}
    ).get(
        "status"
    )

    if continuity not in (
        "PASS",
        "BASELINE"
    ):
        violations.append(
            "QARB_081_CONTINUITY_"
            +str(
                continuity
            )
        )

    return {
        "status":
            "PASS"
            if not violations
            else "HOLD",

        "violations":
            violations,

        "child_return_code":
            child_rc,

        "generation_after_restart":
            int(
                q80s.get(
                    "generation",
                    0
                )
            ),

        "proven_before":
            len(
                before[
                    "proven_tokens"
                ]
            ),

        "proven_after":
            len(
                after[
                    "proven_tokens"
                ]
            ),

        "recyclable_before":
            len(
                before[
                    "recyclable_proven_tokens"
                ]
            ),

        "recyclable_after":
            len(
                after[
                    "recyclable_proven_tokens"
                ]
            ),
    }


def run(
    run_seconds=65.0,
    refresh_seconds=60.0,
    drain_seconds=155.0
):
    root=Path.cwd()

    before=snapshot(
        root
    )

    prior082=before.get(
        "q82_state",
        {}
    )

    if prior082.get(
        "status"
    )!="PASS":
        print(
            "[QARB-083 HOLD] "
            "prior QARB-082 state is not PASS",
            flush=True
        )
        return 2

    print(
        "[QARB-083] RESTART + CONTINUITY "
        "+ ROTATION DURABILITY",
        flush=True
    )

    print(
        "[BASELINE] tokens=%d seen=%d "
        "memory=%d proven=%d recyclable=%d"%(
            len(
                before[
                    "tokens"
                ]
            ),
            len(
                before[
                    "seen"
                ]
            ),
            len(
                before[
                    "memory"
                ]
            ),
            len(
                before[
                    "proven_tokens"
                ]
            ),
            len(
                before[
                    "recyclable_proven_tokens"
                ]
            )
        ),
        flush=True
    )

    print(
        "[RESTART] launching exact certified "
        "QARB-082 in a fresh Python process",
        flush=True
    )

    print(
        "[WINDOW] runtime=%.1fs "
        "refresh=%.1fs drain=%.1fs"%(
            run_seconds,
            refresh_seconds,
            drain_seconds
        ),
        flush=True
    )

    print(
        "[MODE] PAPER_ONLY=True "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    cmd=[
        sys.executable,
        "run_qarb_082_consolidated_one_runtime_cutover.py",
        "--seconds",
        str(
            run_seconds
        ),
        "--refresh-seconds",
        str(
            refresh_seconds
        ),
        "--drain-seconds",
        str(
            drain_seconds
        ),
    ]

    child=subprocess.run(
        cmd,
        cwd=str(
            root
        )
    )

    after=snapshot(
        root
    )

    result=compare(
        before,
        after,
        int(
            child.returncode
        )
    )

    _save(
        root,
        {
            "revision":
                "QARB_083",

            "checked_unix":
                time.time(),

            "before":
                before,

            "after":
                after,

            "result":
                result,

            "execution_authority":
                False,

            "paper_only":
                True,

            "real_money_moved":
                False,
        }
    )

    print(
        "[CONTINUITY] status=%s "
        "violations=%d"%(
            result[
                "status"
            ],
            len(
                result[
                    "violations"
                ]
            )
        ),
        flush=True
    )

    print(
        "[ROTATION_RESTART] "
        "generations=%d child_rc=%d"%(
            result[
                "generation_after_restart"
            ],
            result[
                "child_return_code"
            ]
        ),
        flush=True
    )

    print(
        "[PROVEN_DURABILITY] "
        "before=%d after=%d "
        "recyclable_before=%d "
        "recyclable_after=%d"%(
            result[
                "proven_before"
            ],
            result[
                "proven_after"
            ],
            result[
                "recyclable_before"
            ],
            result[
                "recyclable_after"
            ]
        ),
        flush=True
    )

    for x in result[
        "violations"
    ]:
        print(
            "[HOLD_REASON] "
            +x,
            flush=True
        )

    print(
        "[QARB-083 %s] restart continuity "
        "and rotation durability"%(
            result[
                "status"
            ]
        ),
        flush=True
    )

    print(
        "[MODE] PAPER_ONLY=True "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    return (
        0
        if result[
            "status"
        ]=="PASS"
        else 2
    )


def main(argv=None):
    import argparse

    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--run-seconds",
        type=float,
        default=65.0
    )

    ap.add_argument(
        "--refresh-seconds",
        type=float,
        default=60.0
    )

    ap.add_argument(
        "--drain-seconds",
        type=float,
        default=155.0
    )

    a=ap.parse_args(
        argv
    )

    return run(
        a.run_seconds,
        a.refresh_seconds,
        a.drain_seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
