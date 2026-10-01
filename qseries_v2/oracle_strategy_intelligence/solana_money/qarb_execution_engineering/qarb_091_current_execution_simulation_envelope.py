from __future__ import annotations

import json
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_090_current_executable_liquidity_intake_gate as q90


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_091_current_execution_simulation_envelope.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
MAX_TX_BYTES=1232


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


def intake_rows(root):
    d=_load(
        Path(root)/q90.BINDINGS
    )

    if not isinstance(d,dict):
        raise RuntimeError(
            "QARB_090_BINDINGS_MISSING"
        )

    if d.get("status")!="PASS":
        raise RuntimeError(
            "QARB_090_BINDINGS_NOT_PASS"
        )

    rows=d.get("rows") or []

    if not rows:
        raise RuntimeError(
            "QARB_090_NO_ADMITTED_ROWS"
        )

    return rows


def hydration_bindings(rows):
    out=[]

    for row in rows:
        out.append({
            "token":
                row["token"],

            "pump_pool":
                row["pump_pool"],

            "meteora_meta":
                row["meteora_meta"],

            # Critical:
            # use QARB-090 physically selected size,
            # not older remembered preferred size.
            "size_sol":
                float(
                    row["size_sol"]
                ),
        })

    return out


def validate_intake_row(row):
    required=(
        "token",
        "pump_pool",
        "meteora_meta",
        "size_sol",
        "physical_net_lamports",
        "physical_net_bps",
    )

    missing=[
        x
        for x in required
        if x not in row
    ]

    if missing:
        return (
            False,
            "MISSING:"
            +",".join(missing)
        )

    if not isinstance(
        row["meteora_meta"],
        dict
    ):
        return (
            False,
            "BAD_METEORA_META"
        )

    try:
        if float(
            row["physical_net_bps"]
        )<=0:
            return (
                False,
                "NONPOSITIVE_PHYSICAL_BPS"
            )

        if int(
            row["physical_net_lamports"]
        )<=0:
            return (
                False,
                "NONPOSITIVE_PHYSICAL_NET"
            )

        if float(
            row["size_sol"]
        )<=0:
            return (
                False,
                "BAD_SIZE"
            )

    except Exception:
        return (
            False,
            "BAD_NUMERIC_FIELD"
        )

    return True,"OK"


def candidate_score(row):
    # Prefer:
    # 1. simulation success
    # 2. compiled transaction
    # 3. smaller serialized size
    return (
        0 if (
            row.get("compiled")
            and row.get("sim_err") is None
            and "sim_err" in row
        ) else 1,

        0 if row.get("compiled") else 1,

        int(
            row.get(
                "bytes",
                10**9
            )
        ),
    )


def test_route(
    user,
    pair,
    row,
    extra_alts
):
    size=float(
        row["size_sol"]
    )

    route=q87.compose(
        user,
        pair,
        size
    )

    if (
        route[
            "pre_sim_net_lamports"
        ]<=0
    ):
        return {
            "status":
                "CURRENT_COMPOSE_NONPOSITIVE",

            "size_sol":
                size,

            "current_pre_sim_net_lamports":
                route[
                    "pre_sim_net_lamports"
                ],

            "current_pre_sim_bps":
                route[
                    "pre_sim_bps"
                ],
        }

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

    options=q87.alt_sets(
        route[
            "base_alts"
        ],
        extra_alts
    )

    attempts=[]

    # Intentionally force kp=None.
    # QARB-091 is unsigned simulation certification
    # and must not depend on the private-key gate.
    for candidate in q87.repaired_candidates(
        route
    ):
        x=q87.simulate_candidate(
            user,
            None,
            route,
            candidate,
            options,
            bh
        )

        x["diagnostic"]=(
            q87.diagnostic(x)
        )

        attempts.append(x)

    ranked=sorted(
        attempts,
        key=candidate_score
    )

    winner=next(
        (
            x
            for x in ranked
            if (
                x.get("compiled")
                and "sim_err" in x
                and x.get(
                    "sim_err"
                ) is None
                and int(
                    x.get(
                        "bytes",
                        MAX_TX_BYTES+1
                    )
                )<=MAX_TX_BYTES
            )
        ),
        None
    )

    if winner is None:
        compiled=[
            x
            for x in attempts
            if x.get(
                "compiled"
            )
        ]

        return {
            "status":(
                "COMPILED_NO_CLEAN_SIM"
                if compiled
                else
                "NO_LEGAL_COMPILED_CANDIDATE"
            ),

            "size_sol":
                size,

            "current_pre_sim_net_lamports":
                route[
                    "pre_sim_net_lamports"
                ],

            "current_pre_sim_bps":
                route[
                    "pre_sim_bps"
                ],

            "attempts":
                attempts,
        }

    return {
        "status":
            "UNSIGNED_SIMULATION_PASS",

        "size_sol":
            size,

        "current_pre_sim_net_lamports":
            route[
                "pre_sim_net_lamports"
            ],

        "current_pre_sim_bps":
            route[
                "pre_sim_bps"
            ],

        "selected_candidate":
            winner["name"],

        "selected_bytes":
            int(
                winner["bytes"]
            ),

        "selected_alt_count":
            int(
                winner.get(
                    "alt_count",
                    0
                )
            ),

        "sim_units":
            winner.get(
                "sim_units"
            ),

        "sim_err":
            winner.get(
                "sim_err"
            ),

        # This is expected to remain None in unsigned
        # shadow mode with the old native-only meter.
        # QARB-091 is NOT executable-PnL accounting.
        "sim_pnl_lamports":
            winner.get(
                "sim_pnl_lamports"
            ),

        "attempts":
            attempts,
    }


def run(root=None):
    root=Path(
        root or Path.cwd()
    )

    print(
        "[QARB-091] CURRENT EXECUTION "
        "SIMULATION ENVELOPE",
        flush=True
    )

    print(
        "[SOURCE] QARB-090 admitted routes only",
        flush=True
    )

    print(
        "[PATH] frozen QARB-087 "
        "compose -> repair -> compile -> simulate",
        flush=True
    )

    print(
        "[SIM] unsigned sigVerify=False; "
        "private key not required",
        flush=True
    )

    try:
        rows=intake_rows(
            root
        )

    except RuntimeError as exc:
        print(
            "[QARB-091 HOLD] %s"%(
                exc
            ),
            flush=True
        )

        return 2

    valid=[]

    for row in rows:
        ok,reason=validate_intake_row(
            row
        )

        if not ok:
            print(
                "[INTAKE_REJECT] token=%s "
                "reason=%s"%(
                    str(
                        row.get(
                            "token",
                            ""
                        )
                    )[:10],
                    reason
                ),
                flush=True
            )

            continue

        valid.append(row)

    if not valid:
        print(
            "[QARB-091 HOLD] "
            "no valid QARB-090 rows",
            flush=True
        )

        return 2

    bindings=hydration_bindings(
        valid
    )

    try:
        pairs,_=q87.q86.hydrate(
            root,
            bindings
        )

    except Exception as exc:
        print(
            "[QARB-091 HOLD] "
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

    # We only need a public simulation identity.
    # The keypair is deliberately discarded.
    _,user=c.sim_identity()

    try:
        extra_alts=(
            q87.las.q59.recent_mriya_alt_keys()
        )

    except Exception:
        extra_alts=[]

    results={}

    composed_tokens=0
    compiled_tokens=0
    simulated_tokens=0

    for row in valid:
        token=row["token"]

        pair=pair_map.get(
            token
        )

        result={
            "token":
                token,

            "size_sol":
                float(
                    row["size_sol"]
                ),

            "qarb_090_physical_net_lamports":
                int(
                    row[
                        "physical_net_lamports"
                    ]
                ),

            "qarb_090_physical_net_bps":
                float(
                    row[
                        "physical_net_bps"
                    ]
                ),

            "pump_pool":
                row[
                    "pump_pool"
                ],

            "meteora_pool":
                row[
                    "meteora_meta"
                ][
                    "address"
                ],
        }

        results[token]=result

        if pair is None:
            result[
                "status"
            ]="HYDRATION_PAIR_MISSING"

            continue

        try:
            envelope=test_route(
                user,
                pair,
                row,
                extra_alts
            )

        except Exception as exc:
            result[
                "status"
            ]=(
                "ROUTE_EXCEPTION:"
                +type(exc).__name__
                +":"
                +str(exc)
            )

            continue

        result.update(
            envelope
        )

        composed_tokens+=1

        attempts=envelope.get(
            "attempts",
            []
        )

        if any(
            x.get("compiled")
            for x in attempts
        ):
            compiled_tokens+=1

        if envelope.get(
            "status"
        )=="UNSIGNED_SIMULATION_PASS":
            simulated_tokens+=1

    status=(
        "PASS"
        if simulated_tokens>0
        else "HOLD"
    )

    out={
        "revision":
            "QARB_091",

        "status":
            status,

        "qarb_090_rows":
            len(rows),

        "validated_rows":
            len(valid),

        "hydrated_pairs":
            len(pairs),

        "composed_tokens":
            composed_tokens,

        "compiled_tokens":
            compiled_tokens,

        "unsigned_simulated_tokens":
            simulated_tokens,

        "results":
            results,

        "execution_authority":
            False,

        "paper_only":
            True,

        "real_money_moved":
            False,

        "private_key_required":
            False,

        "created_unix":
            time.time(),
    }

    _save(
        root/STATE,
        out
    )

    for token,result in results.items():
        print(
            "[2S_SIM_ENVELOPE] "
            "token=%s "
            "size=%.6f "
            "q90_bps=%+.2f "
            "status=%s"%(
                token[:10],
                result[
                    "size_sol"
                ],
                result[
                    "qarb_090_physical_net_bps"
                ],
                result.get(
                    "status"
                ),
            ),
            flush=True
        )

        if (
            result.get(
                "status"
            )
            =="UNSIGNED_SIMULATION_PASS"
        ):
            print(
                "[2S_UNSIGNED_SIM_PASS] "
                "token=%s "
                "candidate=%s "
                "bytes=%d "
                "units=%s "
                "sim_err=%s "
                "current_bps=%+.2f"%(
                    token[:10],

                    result[
                        "selected_candidate"
                    ],

                    result[
                        "selected_bytes"
                    ],

                    result.get(
                        "sim_units"
                    ),

                    result.get(
                        "sim_err"
                    ),

                    result[
                        "current_pre_sim_bps"
                    ],
                ),
                flush=True
            )

        else:
            for x in result.get(
                "attempts",
                []
            ):
                print(
                    "[2S_SIM_ATTEMPT] "
                    "token=%s "
                    "candidate=%s "
                    "compiled=%s "
                    "bytes=%s "
                    "sim_err=%s "
                    "diagnostic=%s"%(
                        token[:10],

                        x.get(
                            "name"
                        ),

                        x.get(
                            "compiled"
                        ),

                        x.get(
                            "bytes"
                        ),

                        x.get(
                            "sim_err"
                        ),

                        x.get(
                            "diagnostic"
                        ),
                    ),
                    flush=True
                )

    print(
        "[QARB-091] status=%s "
        "intake=%d "
        "hydrated=%d "
        "composed=%d "
        "compiled=%d "
        "unsigned_simulated=%d"%(
            status,
            len(valid),
            len(pairs),
            composed_tokens,
            compiled_tokens,
            simulated_tokens,
        ),
        flush=True
    )

    print(
        "[MODE] unsigned_simulation_only "
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
