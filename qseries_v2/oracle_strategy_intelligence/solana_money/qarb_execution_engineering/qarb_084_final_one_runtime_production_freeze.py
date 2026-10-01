from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_080_single_runtime_dynamic_mriya_supervisor as q80
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_081_proven_arbitrage_lifecycle_certification as q81
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_082_consolidated_one_runtime_cutover as q82
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_083_restart_continuity_rotation_durability as q83


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_084_final_one_runtime_production_freeze.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

REQUIRED_HORIZONS={
    "2","5","15","30","60","90"
}

SOURCE_FILES={
    "QARB_080":
        Path(q80.__file__),
    "QARB_081":
        Path(q81.__file__),
    "QARB_082":
        Path(q82.__file__),
    "QARB_083":
        Path(q83.__file__),
}


def _load(path,default):
    try:
        return json.loads(
            Path(path).read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return default


def _sha(path):
    return hashlib.sha256(
        Path(path).read_bytes()
    ).hexdigest()


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


def horizon_inventory(root):
    learned=q70._load(
        Path(root)
    ).get(
        "tokens",
        {}
    )

    out={
        h:{
            "samples":0,
            "wins":0,
            "pnl_sol":0.0,
            "tokens":0,
        }
        for h in REQUIRED_HORIZONS
    }

    for token,row in learned.items():
        hs=row.get(
            "horizons",
            {}
        )

        normalized={
            str(k).replace(
                ".0",
                ""
            ):v
            for k,v in hs.items()
        }

        for h in REQUIRED_HORIZONS:
            x=normalized.get(
                h
            )

            if not x:
                continue

            n=int(
                x.get(
                    "samples",
                    0
                )
            )

            w=int(
                x.get(
                    "wins",
                    0
                )
            )

            pnl=float(
                x.get(
                    "pnl_sol",
                    0.0
                )
            )

            out[h][
                "samples"
            ]+=n

            out[h][
                "wins"
            ]+=w

            out[h][
                "pnl_sol"
            ]+=pnl

            if n>0:
                out[h][
                    "tokens"
                ]+=1

    for h,x in out.items():
        x["win_rate"]=(
            x["wins"]/x["samples"]
            if x["samples"]
            else 0.0
        )

    return out


def evaluate(root):
    root=Path(root)

    s80=_load(
        root/q80.STATE,
        {}
    )

    s81=q81.certify(
        root
    )

    s82=_load(
        root/q82.STATE,
        {}
    )

    s83=_load(
        root/q83.STATE,
        {}
    )

    r83=s83.get(
        "result",
        {}
    )

    horizons=horizon_inventory(
        root
    )

    source_hashes={
        name:_sha(path)
        for name,path
        in SOURCE_FILES.items()
    }

    checks={
        "080_generation_ge_2":
            int(
                s80.get(
                    "generation",
                    0
                )
            )>=2,

        "080_transport_clean":
            int(
                s80.get(
                    "transport_failures",
                    0
                )
            )==0,

        "080_usable_nonempty":
            bool(
                s80.get(
                    "usable_tokens",
                    []
                )
            ),

        "080_horizon_max_90":
            float(
                q80.MAX_HORIZON_SECONDS
            )==90.0,

        "081_proven_nonempty":
            int(
                s81.get(
                    "proven_count",
                    0
                )
            )>0,

        "081_recyclable_nonempty":
            bool(
                s81.get(
                    "recyclable_proven_tokens",
                    []
                )
            ),

        "081_continuity_pass":
            s81.get(
                "restart_continuity",
                {}
            ).get(
                "status"
            )=="PASS",

        "082_status_pass":
            s82.get(
                "status"
            )=="PASS",

        "082_runtime_rc_zero":
            s82.get(
                "runtime_return_code"
            ) in (
                None,
                0
            ),

        "082_single_launcher":
            s82.get(
                "single_manual_launcher"
            ) is True,

        "083_status_pass":
            r83.get(
                "status"
            )=="PASS",

        "083_child_rc_zero":
            int(
                r83.get(
                    "child_return_code",
                    -1
                )
            )==0,

        "083_rotation_ge_2":
            int(
                r83.get(
                    "generation_after_restart",
                    0
                )
            )>=2,

        "083_no_violations":
            not r83.get(
                "violations",
                []
            ),

        "authority_080_false":
            q80.EXECUTION_AUTHORITY
            is False,

        "authority_081_false":
            q81.EXECUTION_AUTHORITY
            is False,

        "authority_082_false":
            q82.EXECUTION_AUTHORITY
            is False,

        "authority_083_false":
            q83.EXECUTION_AUTHORITY
            is False,

        "paper_080_true":
            q80.PAPER_ONLY
            is True,

        "paper_081_true":
            q81.PAPER_ONLY
            is True,

        "paper_082_true":
            q82.PAPER_ONLY
            is True,

        "paper_083_true":
            q83.PAPER_ONLY
            is True,

        "money_080_false":
            q80.REAL_MONEY_MOVED
            is False,

        "money_081_false":
            q81.REAL_MONEY_MOVED
            is False,

        "money_082_false":
            q82.REAL_MONEY_MOVED
            is False,

        "money_083_false":
            q83.REAL_MONEY_MOVED
            is False,

        "all_horizons_observed":
            all(
                horizons[h][
                    "samples"
                ]>0
                for h in
                REQUIRED_HORIZONS
            ),
    }

    failed=sorted(
        k
        for k,v
        in checks.items()
        if not v
    )

    certified=not failed

    report={
        "revision":
            "QARB_084",

        "certified":
            certified,

        "frozen":
            certified,

        "checks":
            checks,

        "failed_checks":
            failed,

        "source_hashes":
            source_hashes,

        "runtime_core":
            "QARB_080",

        "classification_core":
            "QARB_081",

        "one_launcher_core":
            "QARB_082",

        "restart_certification_core":
            "QARB_083",

        "proven_count":
            int(
                s81.get(
                    "proven_count",
                    0
                )
            ),

        "research_count":
            int(
                s81.get(
                    "research_count",
                    0
                )
            ),

        "recyclable_proven_tokens":
            list(
                s81.get(
                    "recyclable_proven_tokens",
                    []
                )
            ),

        "horizon_inventory":
            horizons,

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
        report
    )

    return report


def main():
    r=evaluate(
        Path.cwd()
    )

    print(
        "[QARB-084] FINAL ONE-RUNTIME "
        "PRODUCTION CERTIFICATION + FREEZE"
    )

    print(
        "[STACK] 080=runtime 081=classification "
        "082=one-launcher 083=restart-durability"
    )

    print(
        "[PROVEN] count=%d recyclable=%d research=%d"%(
            r[
                "proven_count"
            ],
            len(
                r[
                    "recyclable_proven_tokens"
                ]
            ),
            r[
                "research_count"
            ]
        )
    )

    for h in sorted(
        REQUIRED_HORIZONS,
        key=int
    ):
        x=r[
            "horizon_inventory"
        ][h]

        print(
            "[HORIZON] %ss samples=%d wins=%d "
            "wr=%.1f%% pnl=%+.9f tokens=%d"%(
                h,
                x["samples"],
                x["wins"],
                x["win_rate"]*100.0,
                x["pnl_sol"],
                x["tokens"]
            )
        )

    print(
        "[CERTIFIED] %s [FROZEN] %s"%(
            r["certified"],
            r["frozen"]
        )
    )

    print(
        "[FAILED_CHECKS] %s"%(
            r["failed_checks"]
        )
    )

    print(
        "[MODE] PAPER_ONLY=True "
        "execution_authority=FALSE "
        "real_money_moved=FALSE"
    )

    return (
        0
        if r[
            "certified"
        ]
        else 2
    )


if __name__=="__main__":
    raise SystemExit(
        main()
    )
