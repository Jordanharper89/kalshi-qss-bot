from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_070_persistent_active_profitable_set as q70
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_072_promotion_aging_retirement as q72
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_080_single_runtime_dynamic_mriya_supervisor as q80


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_081_proven_arbitrage_lifecycle_certification.json"
)

MIN_TOKEN_SAMPLES=30
MIN_TOKEN_WIN_RATE=0.80

MIN_HORIZON_SAMPLES=3
MIN_HORIZON_WIN_RATE=0.80

REQUIRED_HORIZONS={
    "2","5","15","30","60","90"
}

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


def _save(path,payload):
    path=Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tmp=path.with_suffix(
        path.suffix+".tmp"
    )

    tmp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )

    tmp.replace(path)


def _hash(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",",":")
        ).encode()
    ).hexdigest()


def horizon_evidence(token_row):
    out={}

    for h,row in token_row.get(
        "horizons",
        {}
    ).items():

        h=str(h)

        n=int(
            row.get(
                "samples",
                0
            )
        )

        wins=int(
            row.get(
                "wins",
                0
            )
        )

        pnl=float(
            row.get(
                "pnl_sol",
                0.0
            )
        )

        wr=(
            wins/n
            if n
            else 0.0
        )

        proven=(
            n>=MIN_HORIZON_SAMPLES
            and wr>=MIN_HORIZON_WIN_RATE
            and pnl>0.0
        )

        out[h]={
            "samples":n,
            "wins":wins,
            "win_rate":wr,
            "pnl_sol":pnl,
            "proven":proven,
        }

    return out


def classify_token(
    token,
    token_row,
    lifecycle
):
    samples=int(
        token_row.get(
            "samples",
            0
        )
    )

    wins=int(
        token_row.get(
            "wins",
            0
        )
    )

    pnl=float(
        token_row.get(
            "pnl_sol",
            0.0
        )
    )

    wr=(
        wins/samples
        if samples
        else 0.0
    )

    horizons=horizon_evidence(
        token_row
    )

    proven_horizons=sorted(
        h
        for h,x in horizons.items()
        if x["proven"]
    )

    reasons=[]

    if lifecycle not in ("ACTIVE","RECHECK"):
        reasons.append(
            "LIFECYCLE_NOT_RECYCLABLE"
        )

    if samples<MIN_TOKEN_SAMPLES:
        reasons.append(
            "INSUFFICIENT_TOKEN_SAMPLES"
        )

    if wr<MIN_TOKEN_WIN_RATE:
        reasons.append(
            "TOKEN_WIN_RATE_BELOW_PROVEN_GATE"
        )

    if pnl<=0:
        reasons.append(
            "TOKEN_CUMULATIVE_PNL_NOT_POSITIVE"
        )

    if not proven_horizons:
        reasons.append(
            "NO_PROVEN_HORIZON"
        )

    classification=(
        "PROVEN_PAPER_ARBITRAGE"
        if not reasons
        else "RESEARCH"
    )

    return {
        "token":token,
        "classification":classification,
        "lifecycle":lifecycle,
        "requires_live_recheck":(
            lifecycle=="RECHECK"
        ),
        "samples":samples,
        "wins":wins,
        "win_rate":wr,
        "pnl_sol":pnl,
        "proven_horizons":
            proven_horizons,
        "horizons":
            horizons,
        "hold_reasons":
            reasons,
    }


def continuity_check(
    previous,
    current_tokens,
    current_seen,
    current_memory
):
    if not previous:
        return {
            "status":"BASELINE",
            "violations":[],
        }

    violations=[]

    prior_tokens=previous.get(
        "continuity_anchor",
        {}
    ).get(
        "tokens",
        {}
    )

    for token,old in prior_tokens.items():
        cur=current_tokens.get(
            token
        )

        if cur is None:
            violations.append(
                "TOKEN_HISTORY_LOST:"+token
            )
            continue

        if int(
            cur.get(
                "samples",
                0
            )
        ) < int(
            old.get(
                "samples",
                0
            )
        ):
            violations.append(
                "SAMPLE_COUNT_ROLLBACK:"+token
            )

        if int(
            cur.get(
                "wins",
                0
            )
        ) < int(
            old.get(
                "wins",
                0
            )
        ):
            violations.append(
                "WIN_COUNT_ROLLBACK:"+token
            )

    prior_seen=set(
        previous.get(
            "continuity_anchor",
            {}
        ).get(
            "seen_tokens",
            []
        )
    )

    if not prior_seen.issubset(
        current_seen
    ):
        violations.append(
            "SEEN_TOKEN_HISTORY_ROLLBACK"
        )

    prior_memory=set(
        previous.get(
            "continuity_anchor",
            {}
        ).get(
            "memory_tokens",
            []
        )
    )

    if not prior_memory.issubset(
        current_memory
    ):
        violations.append(
            "BINDING_MEMORY_ROLLBACK"
        )

    return {
        "status":
            "PASS"
            if not violations
            else "HOLD",
        "violations":
            violations,
    }


def certify(root):
    root=Path(root)

    previous=_load(
        root/STATE,
        {}
    )

    learned=q70._load(
        root
    )

    lifecycle=q72.run(
        root
    )

    learned_tokens=learned.get(
        "tokens",
        {}
    )

    lifecycle_tokens=lifecycle.get(
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

    presence=set(
        _load(
            root/q80.PRESENCE,
            {"tokens":[]}
        ).get(
            "tokens",
            []
        )
    )

    memory_rows=_load(
        root/q80.MEMORY,
        {"rows":{}}
    ).get(
        "rows",
        {}
    )

    memory=set(
        memory_rows
    )

    rows={}

    for token,x in sorted(
        learned_tokens.items()
    ):
        life=(
            lifecycle_tokens.get(
                token,
                {}
            ).get(
                "lifecycle",
                x.get(
                    "status",
                    "OBSERVE"
                )
            )
        )

        rows[token]=classify_token(
            token,
            x,
            life
        )

    proven={
        token:x
        for token,x in rows.items()
        if x["classification"]
        =="PROVEN_PAPER_ARBITRAGE"
    }

    research={
        token:x
        for token,x in rows.items()
        if x["classification"]
        =="RESEARCH"
    }

    recyclable=sorted(
        set(proven)
        &memory
    )

    proven_unbound=sorted(
        set(proven)
        -memory
    )

    continuity=continuity_check(
        previous,
        learned_tokens,
        seen,
        memory
    )

    seen_presence_ok=(
        presence.issubset(
            seen
        )
    )

    report={
        "revision":"QARB_081",
        "policy":{
            "min_token_samples":
                MIN_TOKEN_SAMPLES,
            "min_token_win_rate":
                MIN_TOKEN_WIN_RATE,
            "min_horizon_samples":
                MIN_HORIZON_SAMPLES,
            "min_horizon_win_rate":
                MIN_HORIZON_WIN_RATE,
        },
        "proven_count":
            len(proven),
        "research_count":
            len(research),
        "proven_tokens":
            proven,
        "research_tokens":
            research,
        "recyclable_proven_tokens":
            recyclable,
        "proven_unbound_tokens":
            proven_unbound,
        "seen_count":
            len(seen),
        "presence_count":
            len(presence),
        "memory_count":
            len(memory),
        "presence_subset_seen":
            seen_presence_ok,
        "restart_continuity":
            continuity,
        "continuity_anchor":{
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
                }
                for token,x
                in learned_tokens.items()
            },
            "seen_tokens":
                sorted(seen),
            "memory_tokens":
                sorted(memory),
        },
        "state_hash":
            _hash(
                {
                    "rows":rows,
                    "seen":
                        sorted(seen),
                    "memory":
                        sorted(memory),
                }
            ),
        "execution_authority":
            False,
        "paper_only":
            True,
        "real_money_moved":
            False,
    }

    _save(
        root/STATE,
        report
    )

    return report


def main():
    r=certify(
        Path.cwd()
    )

    print(
        "[QARB-081] PROVEN PAPER ARBITRAGE "
        "LIFECYCLE CERTIFICATION"
    )

    print(
        "[LANES] proven=%d research=%d"%(
            r["proven_count"],
            r["research_count"]
        )
    )

    for token,x in r[
        "proven_tokens"
    ].items():
        print(
            "[PROVEN_PAPER] token=%s "
            "samples=%d wins=%d "
            "win_rate=%.1f%% pnl=%+.9f "
            "horizons=%s"%(
                token[:10],
                x["samples"],
                x["wins"],
                x["win_rate"]*100.0,
                x["pnl_sol"],
                ",".join(
                    x["proven_horizons"]
                )
            )
        )

        if x["requires_live_recheck"]:
            print(
                "[LIVE_RECHECK_REQUIRED] token=%s "
                "historical_proven=True"%(
                    token[:10]
                )
            )

    print(
        "[RECYCLE] proven_bound=%d "
        "proven_unbound=%d"%(
            len(
                r[
                    "recyclable_proven_tokens"
                ]
            ),
            len(
                r[
                    "proven_unbound_tokens"
                ]
            )
        )
    )

    print(
        "[RESURRECTION_STATE] "
        "presence_subset_seen=%s"%(
            r["presence_subset_seen"]
        )
    )

    print(
        "[RESTART_CONTINUITY] "
        "status=%s violations=%d"%(
            r[
                "restart_continuity"
            ]["status"],
            len(
                r[
                    "restart_continuity"
                ]["violations"]
            )
        )
    )

    print(
        "[POLICY] research may be broad; "
        "proven-paper lane requires >=%d samples "
        "and >=%.0f%% overall win rate"%(
            MIN_TOKEN_SAMPLES,
            MIN_TOKEN_WIN_RATE*100
        )
    )

    print(
        "[MODE] PAPER_ONLY=True "
        "execution_authority=FALSE "
        "real_money_moved=FALSE"
    )

    return 0


if __name__=="__main__":
    raise SystemExit(
        main()
    )
