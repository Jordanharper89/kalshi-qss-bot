from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_080_single_runtime_dynamic_mriya_supervisor as q80
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_081_proven_arbitrage_lifecycle_certification as q81


STATE=Path(
    "runtime_state/qseries/"
    "qarb_execution_engineering/"
    "qarb_082_consolidated_one_runtime_cutover.json"
)

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


def certification_summary(root):
    r=q81.certify(
        Path(root)
    )

    return {
        "proven_count":
            int(
                r.get(
                    "proven_count",
                    0
                )
            ),
        "research_count":
            int(
                r.get(
                    "research_count",
                    0
                )
            ),
        "proven_tokens":
            sorted(
                r.get(
                    "proven_tokens",
                    {}
                )
            ),
        "recyclable_proven_tokens":
            sorted(
                r.get(
                    "recyclable_proven_tokens",
                    []
                )
            ),
        "restart_continuity":
            dict(
                r.get(
                    "restart_continuity",
                    {}
                )
            ),
        "execution_authority":
            False,
    }


def run(
    seconds=None,
    refresh_seconds=60.0,
    drain_seconds=155.0
):
    root=Path.cwd()

    before=certification_summary(
        root
    )

    print(
        "[QARB-082] CONSOLIDATED ONE-RUNTIME CUTOVER",
        flush=True
    )

    print(
        "[CORE] QARB-080 owns discovery, rotation, "
        "hydration, WS transport, paper outcomes and learning",
        flush=True
    )

    print(
        "[CLASSIFIER] QARB-081 proven/research "
        "certification is internal to this launcher",
        flush=True
    )

    print(
        "[PRECHECK] proven=%d research=%d "
        "recyclable=%d"%(
            before[
                "proven_count"
            ],
            before[
                "research_count"
            ],
            len(
                before[
                    "recyclable_proven_tokens"
                ]
            )
        ),
        flush=True
    )

    _save(
        root,
        {
            "revision":
                "QARB_082",
            "phase":
                "STARTING",
            "started_unix":
                time.time(),
            "precheck":
                before,
            "single_manual_launcher":
                True,
            "runtime_core":
                "QARB_080",
            "classification_core":
                "QARB_081",
            "execution_authority":
                False,
            "paper_only":
                True,
            "real_money_moved":
                False,
        }
    )

    rc=q80.run(
        seconds=seconds,
        refresh_seconds=
            refresh_seconds,
        drain_seconds=
            drain_seconds
    )

    after=certification_summary(
        root
    )

    continuity=(
        after.get(
            "restart_continuity",
            {}
        ).get(
            "status"
        )
    )

    runtime_ok=(
        rc in (
            None,
            0
        )
    )

    certification_ok=(
        continuity in (
            "PASS",
            "BASELINE"
        )
    )

    status=(
        "PASS"
        if (
            runtime_ok
            and certification_ok
        )
        else "HOLD"
    )

    _save(
        root,
        {
            "revision":
                "QARB_082",
            "phase":
                "COMPLETE",
            "completed_unix":
                time.time(),
            "precheck":
                before,
            "postcheck":
                after,
            "runtime_return_code":
                rc,
            "single_manual_launcher":
                True,
            "runtime_core":
                "QARB_080",
            "classification_core":
                "QARB_081",
            "status":
                status,
            "execution_authority":
                False,
            "paper_only":
                True,
            "real_money_moved":
                False,
        }
    )

    print(
        "[POSTCHECK] proven=%d research=%d "
        "recyclable=%d continuity=%s"%(
            after[
                "proven_count"
            ],
            after[
                "research_count"
            ],
            len(
                after[
                    "recyclable_proven_tokens"
                ]
            ),
            continuity
        ),
        flush=True
    )

    print(
        "[ONE_RUNTIME] status=%s "
        "manual_launchers=1"%status,
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
        if status=="PASS"
        else 2
    )


def main(argv=None):
    import argparse

    ap=argparse.ArgumentParser()

    ap.add_argument(
        "--seconds",
        type=float,
        default=None
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
        seconds=
            a.seconds,
        refresh_seconds=
            a.refresh_seconds,
        drain_seconds=
            a.drain_seconds
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
