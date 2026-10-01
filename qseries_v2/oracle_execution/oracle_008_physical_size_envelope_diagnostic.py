from __future__ import annotations

import base64
import json
import time
from pathlib import Path

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine as q
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False

SIZE_SOL=(
    0.001,0.002,0.005,0.010,0.025,0.050,
    0.100,0.180,0.280,0.500,0.900,1.100,1.400,
)

OUT=Path(
    "runtime_state/oracle/oracle_live_execution/"
    "oracle_008_physical_size_envelope.json"
)


def lamports(sol):
    return int(round(float(sol)*1_000_000_000))


def max_quote_envelope(principal):
    bps=int(q.base.q87.las.q59.SLIPPAGE_BPS)
    return (int(principal)*(10000+bps)+9999)//10000


def pump_min_base_out_for_size(pump_ix,principal):
    raw=base64.b64decode(pump_ix.get("data") or "")

    BUY=bytes([102,6,61,18,1,218,235,234])
    BUY_EXACT=bytes([198,46,21,82,180,217,232,112])

    if len(raw)<24:
        raise RuntimeError("PUMP_DATA_TOO_SHORT")

    disc=raw[:8]
    a=int.from_bytes(raw[8:16],"little")
    b=int.from_bytes(raw[16:24],"little")

    if disc==BUY:
        allowed=max_quote_envelope(principal)

        if b>allowed:
            raise RuntimeError(
                "PUMP_MAX_QUOTE_OUTSIDE_SIZE_ENVELOPE:"
                +str(b)+":allowed="+str(allowed)
            )

        if a<=0:
            raise RuntimeError("PUMP_BASE_AMOUNT_ZERO")

        return {
            "instruction":"BUY",
            "base_min":a,
            "quote_ceiling":b,
        }

    if disc==BUY_EXACT:
        if a>int(principal):
            raise RuntimeError(
                "PUMP_EXACT_INPUT_EXCEEDS_SIZE:"+str(a)
            )

        if b<=0:
            raise RuntimeError("PUMP_MINIMUM_ZERO")

        return {
            "instruction":"BUY_EXACT_QUOTE_IN",
            "base_min":b,
            "quote_ceiling":a,
        }

    raise RuntimeError(
        "PUMP_UNKNOWN_BUY_DISCRIMINATOR:"+disc.hex()
    )


def physical_route_for_size(user,pair,principal):
    principal=int(principal)

    pump_ixs,pump_quote_out=(
        q.base.q87.las.q59.native_pump_buy_ixs(
            user,
            pair.pump_pool,
            principal
        )
    )

    pos=[
        i for i,x in enumerate(pump_ixs)
        if x.get("programId")==q.base.q87.c.PUMP
    ]

    if len(pos)!=1:
        raise RuntimeError("PUMP_IX_COUNT:"+str(len(pos)))

    pi=pos[0]

    parsed=pump_min_base_out_for_size(
        pump_ixs[pi],
        principal
    )

    received=q.net_received(
        pair.token,
        parsed["base_min"]
    )

    spendable=int(received["net"])

    if spendable<=0:
        raise RuntimeError("PUMP_NET_MINIMUM_ZERO")

    meteora=q.meteora_swap(
        user,
        pair,
        spendable
    )

    if int(meteora["consumed"])!=spendable:
        raise RuntimeError("METEORA_PARTIAL_INPUT")

    guaranteed_end=int(meteora["min_out"])
    quote_end=int(meteora["out"])

    guaranteed_net=guaranteed_end-principal
    quote_net=quote_end-principal

    pre=list(pump_ixs[:pi])
    post=list(pump_ixs[pi+1:])

    full=(
        pre
        +[pump_ixs[pi]]
        +meteora["instructions"]
        +post
    )

    return {
        "token":pair.token,
        "start_lamports":principal,
        "pump_instruction":parsed["instruction"],
        "pump_quote_ceiling":parsed["quote_ceiling"],
        "pump_quote_out":int(pump_quote_out),
        "pump_minimum_out":parsed["base_min"],
        "pump_transfer_fee":int(received["fee"]),
        "pump_spendable_out":spendable,
        "meteora_quote_out":quote_end,
        "meteora_min_out":guaranteed_end,
        "meteora_bin_depth":meteora["depth"],
        "quote_net_lamports":quote_net,
        "quote_bps":quote_net/principal*10000.0,
        "guaranteed_net_lamports":guaranteed_net,
        "guaranteed_bps":guaranteed_net/principal*10000.0,
        "base_alts":[],
        "original_candidates":[
            ("ORACLE_SIZE_ENVELOPE_FULL",full)
        ],
    }


def inspect_packet(user,kp,route):
    try:
        compiled=q.base.compile_signed(
            user,
            kp,
            route,
            "ORACLE_SIZE_ENVELOPE_FULL"
        )
    except Exception as exc:
        return {
            "legal_packet":False,
            "packet_reason":type(exc).__name__+":"+str(exc),
            "bytes":None,
        }

    if not compiled.get("ok"):
        return {
            "legal_packet":False,
            "packet_reason":compiled.get("reason"),
            "bytes":None,
            "attempts":compiled.get("attempts",[]),
        }

    return {
        "legal_packet":True,
        "packet_reason":None,
        "bytes":int(compiled["bytes"]),
    }


def run():
    root=Path.cwd()
    kp,user=q.base.require_keypair()

    balance=int(
        q.rpc(
            "getBalance",
            [user,{"commitment":"confirmed"}]
        )["value"]
    )

    print(
        "[ORACLE-008] PHYSICAL SIZE ENVELOPE DIAGNOSTIC",
        flush=True
    )

    print(
        "[MODE] PAPER_ONLY=True "
        "execution_authority=FALSE "
        "real_money_moved=FALSE",
        flush=True
    )

    print(
        "[WALLET] %s"%user,
        flush=True
    )

    print(
        "[BALANCE] %.9f SOL"%(
            balance/1e9
        ),
        flush=True
    )

    print(
        "[LIVE_CANARY] remains=0.001_SOL",
        flush=True
    )

    print(
        "[SIZE_LADDER] %s"%(
            ",".join(
                "%.3f"%x
                for x in SIZE_SOL
            )
        ),
        flush=True
    )

    rows=q.live_universe_rows(
        root
    )

    if not rows:
        print(
            "[HOLD] "
            "no fresh exact-bound "
            "PumpSwap->Meteora rows",
            flush=True
        )
        return 2

    pair_map=q.base.hydrate_rows(
        root,
        rows
    )

    results=[]
    positives=[]

    for row in rows:
        token=row["token"]

        pair=pair_map.get(
            token
        )

        if pair is None:
            print(
                "[SIZE_TOKEN_SKIP] "
                "token=%s reason=PAIR_MISSING"%(
                    token[:10]
                ),
                flush=True
            )
            continue

        print(
            "[SIZE_TOKEN] "
            "token=%s"%(
                token[:10]
            ),
            flush=True
        )

        for sol in SIZE_SOL:
            principal=lamports(
                sol
            )

            rec={
                "token":
                    token,

                "size_sol":
                    sol,

                "principal_lamports":
                    principal,

                "wallet_fundable":
                    balance>=principal,
            }

            try:
                route=physical_route_for_size(
                    user,
                    pair,
                    principal
                )

                packet=inspect_packet(
                    user,
                    kp,
                    route
                )

                rec.update({
                    "status":
                        "MEASURED",

                    "quote_net_lamports":
                        route[
                            "quote_net_lamports"
                        ],

                    "quote_bps":
                        route[
                            "quote_bps"
                        ],

                    "guaranteed_net_lamports":
                        route[
                            "guaranteed_net_lamports"
                        ],

                    "guaranteed_bps":
                        route[
                            "guaranteed_bps"
                        ],

                    "pump_transfer_fee":
                        route[
                            "pump_transfer_fee"
                        ],

                    "meteora_bin_depth":
                        route[
                            "meteora_bin_depth"
                        ],

                    "legal_packet":
                        packet[
                            "legal_packet"
                        ],

                    "packet_reason":
                        packet[
                            "packet_reason"
                        ],

                    "bytes":
                        packet[
                            "bytes"
                        ],
                })

                positive=(
                    route[
                        "guaranteed_net_lamports"
                    ]>0
                    and packet[
                        "legal_packet"
                    ]
                )

                rec[
                    "positive_physical_envelope"
                ]=positive

                if positive:
                    positives.append(
                        rec
                    )

                print(
                    "[SIZE_POINT] "
                    "token=%s "
                    "size=%.3f "
                    "quote=%+.9f_SOL "
                    "guaranteed=%+.9f_SOL "
                    "gbps=%+.2f "
                    "packet=%s "
                    "bytes=%s "
                    "wallet_fundable=%s"%(
                        token[:10],
                        sol,

                        route[
                            "quote_net_lamports"
                        ]/1e9,

                        route[
                            "guaranteed_net_lamports"
                        ]/1e9,

                        route[
                            "guaranteed_bps"
                        ],

                        (
                            "YES"
                            if packet[
                                "legal_packet"
                            ]
                            else "NO"
                        ),

                        str(
                            packet[
                                "bytes"
                            ]
                        ),

                        (
                            "YES"
                            if rec[
                                "wallet_fundable"
                            ]
                            else "NO"
                        ),
                    ),
                    flush=True
                )

            except Exception as exc:
                rec.update({
                    "status":
                        "REJECT",

                    "reason":
                        type(exc).__name__
                        +":"
                        +str(exc),

                    "positive_physical_envelope":
                        False,
                })

                print(
                    "[SIZE_REJECT] "
                    "token=%s "
                    "size=%.3f "
                    "reason=%s"%(
                        token[:10],
                        sol,
                        rec[
                            "reason"
                        ],
                    ),
                    flush=True
                )

            results.append(
                rec
            )

    positives.sort(
        key=lambda x:(
            x[
                "guaranteed_bps"
            ],
            x[
                "guaranteed_net_lamports"
            ]
        ),
        reverse=True
    )

    fundable=[
        x
        for x in positives
        if x[
            "wallet_fundable"
        ]
    ]

    report={
        "revision":
            "ORACLE_008",

        "paper_only":
            True,

        "execution_authority":
            False,

        "real_money_moved":
            False,

        "wallet":
            user,

        "wallet_balance_lamports":
            balance,

        "live_canary_lamports":
            q.MICRO_LAMPORTS,

        "sizes_sol":
            list(
                SIZE_SOL
            ),

        "results":
            results,

        "positive_points":
            positives,

        "wallet_fundable_positive_points":
            fundable,

        "created_unix":
            time.time(),
    }

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUT.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True
        ),
        encoding="utf-8"
    )

    print(
        "[SIZE_SUMMARY] "
        "measured=%d "
        "positive=%d "
        "wallet_fundable_positive=%d"%(
            sum(
                x.get(
                    "status"
                )=="MEASURED"
                for x in results
            ),
            len(
                positives
            ),
            len(
                fundable
            ),
        ),
        flush=True
    )

    if positives:
        best=positives[0]

        print(
            "[BEST_PHYSICAL_ENVELOPE] "
            "token=%s "
            "size=%.3f "
            "guaranteed=%+.9f_SOL "
            "bps=%+.2f "
            "wallet_fundable=%s"%(
                best[
                    "token"
                ][:10],

                best[
                    "size_sol"
                ],

                best[
                    "guaranteed_net_lamports"
                ]/1e9,

                best[
                    "guaranteed_bps"
                ],

                (
                    "YES"
                    if best[
                        "wallet_fundable"
                    ]
                    else "NO"
                ),
            ),
            flush=True
        )

    else:
        print(
            "[ENVELOPE_HOLD] "
            "no positive physical size "
            "found across ladder",
            flush=True
        )

    print(
        "[REPORT] %s"%OUT,
        flush=True
    )

    return 0


if __name__=="__main__":
    raise SystemExit(
        run()
    )
