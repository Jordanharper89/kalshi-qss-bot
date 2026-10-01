from pathlib import Path
import py_compile

ROOT=Path.cwd()
OUTDIR=ROOT/"qseries_v2/oracle_execution"
MODULE=OUTDIR/"oracle_008_physical_size_envelope_diagnostic.py"
LAUNCHER=ROOT/"run_oracle_size_envelope.py"
TEST=ROOT/"test_oracle_008_physical_size_envelope_diagnostic.py"
ENGINE=OUTDIR/"oracle_003_unified_physical_execution_engine.py"

if not ENGINE.is_file():
    raise SystemExit("[FAIL] Oracle unified physical engine missing")

MODULE.write_text(r'''
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
'''.strip()+"\n",encoding="utf-8")

py_compile.compile(
    str(MODULE),
    doraise=True
)

LAUNCHER.write_text(
r'''
import getpass
import os

from qseries_v2.oracle_execution.oracle_008_physical_size_envelope_diagnostic import run


def main():
    os.environ[
        "QSB_SOLANA_PRIVATE_KEY"
    ]=getpass.getpass(
        "Private key (hidden): "
    )

    return run()


if __name__=="__main__":
    raise SystemExit(
        main()
    )
'''.strip()+"\n",
    encoding="utf-8"
)

py_compile.compile(
    str(LAUNCHER),
    doraise=True
)

TEST.write_text(
r'''
import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_008_physical_size_envelope_diagnostic as q
)


class T(unittest.TestCase):

    def test_paper_only(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


    def test_ladder(self):
        for x in (
            0.001,
            0.005,
            0.05,
            0.1,
            0.18,
            0.28,
            0.5,
            0.9,
            1.1,
            1.4,
        ):
            self.assertIn(
                x,
                q.SIZE_SOL
            )


    def test_parameterized_pump(self):
        s=inspect.getsource(
            q.physical_route_for_size
        )

        self.assertIn(
            "principal",
            s
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )


    def test_meteora(self):
        s=inspect.getsource(
            q.physical_route_for_size
        )

        self.assertIn(
            "q.meteora_swap",
            s
        )


    def test_packet_legality(self):
        s=inspect.getsource(
            q.inspect_packet
        )

        self.assertIn(
            "compile_signed",
            s
        )


    def test_no_broadcast(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "send_once(",
            s
        )

        self.assertNotIn(
            "sendTransaction",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
'''.strip()+"\n",
    encoding="utf-8"
)

py_compile.compile(
    str(TEST),
    doraise=True
)

print(
    "[PASS] ORACLE-008 physical size-envelope diagnostic installed"
)

print(
    "[STRATEGY] PumpSwap -> Meteora DLMM"
)

print(
    "[SIZES] 0.001 through 1.400 SOL ladder"
)

print(
    "[PHYSICAL] Pump minimum + Token-2022 + Meteora minimum"
)

print(
    "[PACKET] legal signed packet size checked"
)

print(
    "[WALLET] fundability reported separately"
)

print(
    "[LIVE_CANARY] unchanged at 0.001 SOL"
)

print(
    "[BROADCAST] disabled"
)

print(
    "[OWNER] ORACLE"
)