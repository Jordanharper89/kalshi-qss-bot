from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_execution_engineering"

Q87=S/"qarb_087_two_second_compaction_liquidity_repair.py"
CORE=R/"qseries_v2/oracle_strategy_intelligence/solana_money/native_atomic_money_machine/core.py"

M=S/"qarb_088_two_second_executable_profit_accounting.py"
T=R/"test_qarb_088_two_second_executable_profit_accounting.py"
U=R/"run_qarb_088_two_second_executable_profit_accounting.py"

for p in (Q87,CORE):
    if not p.is_file():
        raise SystemExit("[FAIL] dependency missing: "+str(p))

s87=Q87.read_text(encoding="utf-8")
score=CORE.read_text(encoding="utf-8")

guards=[
    ("087 compose","def compose(" in s87),
    ("087 repaired candidates","def repaired_candidates(" in s87),
    ("087 compile candidate","def compile_candidate(" in s87),
    ("087 size ladder","def size_ladder(" in s87),
    ("core sim identity","def sim_identity(" in score),
    ("core ata","def ata(" in score),
    ("core rpc","def rpc(" in score),
    ("core signed","def signed_tx(" in score),
]

bad=[name for name,ok in guards if not ok]

if bad:
    raise SystemExit(
        "[FAIL] exact current source contract changed: "+repr(bad)
    )

module=r'''from __future__ import annotations

import base64
import json
import struct
import time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_atomic_simulation as las
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87


STATE=Path(
    "runtime_state/qseries/qarb_execution_engineering/"
    "qarb_088_two_second_executable_profit_accounting.json"
)

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
MAX_TX_BYTES=1232


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


def token_amount_from_data(raw):
    if raw is None:
        return 0

    if len(raw)<72:
        raise RuntimeError(
            "TOKEN_ACCOUNT_SHORT"
        )

    return int(
        struct.unpack_from(
            "<Q",
            raw,
            64
        )[0]
    )


def decode_rpc_account(row):
    if not row:
        return {
            "exists":False,
            "lamports":0,
            "owner":None,
            "data":None,
        }

    data=row.get("data")
    raw=None

    if isinstance(data,list) and data:
        raw=base64.b64decode(
            data[0]
        )

    return {
        "exists":True,
        "lamports":int(
            row.get(
                "lamports",
                0
            )
        ),
        "owner":row.get("owner"),
        "data":raw,
    }


def live_account(addr):
    x=c.rpc(
        "getAccountInfo",
        [
            addr,
            {
                "encoding":"base64",
                "commitment":"processed"
            }
        ]
    )

    return decode_rpc_account(
        (x or {}).get("value")
    )


def token_snapshot(addr):
    x=live_account(addr)

    return {
        "exists":x["exists"],
        "lamports":x["lamports"],
        "amount":(
            token_amount_from_data(
                x["data"]
            )
            if x["exists"]
            else 0
        ),
        "owner":x["owner"],
    }


def native_balance(addr):
    return int(
        c.rpc(
            "getBalance",
            [
                addr,
                {
                    "commitment":"processed"
                }
            ]
        )["value"]
    )


def wealth_lamports(native,wsol):
    # IMPORTANT:
    # A native WSOL token account's lamports already contain
    # the wrapped SOL principal plus rent reserve.
    #
    # Adding token amount again double-counts the wrapped SOL.
    return (
        int(native)
        +int(wsol["lamports"])
    )


def require_local_identity(kp,user):
    if kp is None:
        raise RuntimeError(
            "QARB_088_LOCAL_SOLANA_PRIVATE_KEY_REQUIRED"
        )

    actual=str(
        kp.pubkey()
    )

    if actual!=user:
        raise RuntimeError(
            "QARB_088_SIGNER_IDENTITY_MISMATCH"
        )

    return actual


def derive_accounts(user,token):
    wsol_program=c.account(
        c.WSOL
    )[1]

    token_program=c.account(
        token
    )[1]

    return {
        "wsol_ata":
            c.ata(
                user,
                c.WSOL,
                wsol_program
            ),

        "token_ata":
            c.ata(
                user,
                token,
                token_program
            ),

        "wsol_program":
            wsol_program,

        "token_program":
            token_program,
    }


def candidate_pubkeys(candidate):
    out=set()

    for ix in candidate[
        "instructions"
    ]:
        out.add(
            ix.get("programId")
        )

        for a in ix.get(
            "accounts"
        ) or []:
            out.add(
                a.get("pubkey")
            )

    out.discard(None)

    return out


def verify_account_lineage(
    user,
    token,
    candidate
):
    accounts=derive_accounts(
        user,
        token
    )

    keys=candidate_pubkeys(
        candidate
    )

    missing=[]

    if user not in keys:
        missing.append(
            "PAYER"
        )

    if accounts[
        "wsol_ata"
    ] not in keys:
        missing.append(
            "WSOL_ATA"
        )

    if accounts[
        "token_ata"
    ] not in keys:
        missing.append(
            "TOKEN_ATA"
        )

    return accounts,missing


def pre_snapshot(
    user,
    token,
    accounts=None
):
    a=(
        accounts
        if accounts is not None
        else derive_accounts(
            user,
            token
        )
    )

    return {
        **a,

        "native_lamports":
            native_balance(
                user
            ),

        "wsol":
            token_snapshot(
                a[
                    "wsol_ata"
                ]
            ),

        "token":
            token_snapshot(
                a[
                    "token_ata"
                ]
            ),
    }


def simulated_account(
    row,
    is_token
):
    x=decode_rpc_account(
        row
    )

    if not x[
        "exists"
    ]:
        return {
            "exists":False,
            "lamports":0,
            "amount":0,
            "owner":None,
        }

    return {
        "exists":True,

        "lamports":
            x["lamports"],

        "amount":(
            token_amount_from_data(
                x["data"]
            )
            if is_token
            else 0
        ),

        "owner":
            x["owner"],
    }


def estimate_fee(message):
    try:
        result=c.rpc(
            "getFeeForMessage",
            [
                base64.b64encode(
                    message
                ).decode(),
                {
                    "commitment":
                        "processed"
                }
            ]
        )

        value=(
            (result or {}).get(
                "value"
            )
        )

        return (
            None
            if value is None
            else int(value)
        )

    except Exception:
        return None


def simulate_wealth(
    raw,
    message,
    user,
    token,
    accounts
):
    pre=pre_snapshot(
        user,
        token,
        accounts
    )

    addresses=[
        user,
        accounts[
            "wsol_ata"
        ],
        accounts[
            "token_ata"
        ],
    ]

    v=c.rpc(
        "simulateTransaction",
        [
            base64.b64encode(
                raw
            ).decode(),

            {
                "encoding":"base64",

                # QARB-088 now requires the actual local signer.
                "sigVerify":True,

                "commitment":
                    "processed",

                "accounts":{
                    "encoding":
                        "base64",

                    "addresses":
                        addresses,
                }
            }
        ]
    )

    returned=list(
        v.get(
            "accounts"
        )
        or []
    )

    while len(returned)<3:
        returned.append(
            None
        )

    # The payer must always be returned.
    if returned[0] is None:
        raise RuntimeError(
            "SIMULATED_PAYER_ACCOUNT_NOT_RETURNED"
        )

    post_native=int(
        returned[0].get(
            "lamports",
            0
        )
    )

    post_wsol=simulated_account(
        returned[1],
        True
    )

    post_token=simulated_account(
        returned[2],
        True
    )

    pre_wealth=wealth_lamports(
        pre[
            "native_lamports"
        ],
        pre[
            "wsol"
        ]
    )

    post_wealth=wealth_lamports(
        post_native,
        post_wsol
    )

    gross_delta=(
        post_wealth
        -pre_wealth
    )

    fee=estimate_fee(
        message
    )

    net_after_fee=(
        gross_delta-fee
        if fee is not None
        else None
    )

    token_delta=(
        post_token[
            "amount"
        ]
        -pre[
            "token"
        ][
            "amount"
        ]
    )

    return {
        "err":
            v.get("err"),

        "units":
            v.get(
                "unitsConsumed"
            ),

        "pre_native_lamports":
            pre[
                "native_lamports"
            ],

        "post_native_lamports":
            post_native,

        "native_delta_lamports":
            post_native
            -pre[
                "native_lamports"
            ],

        "pre_wsol_account_lamports":
            pre[
                "wsol"
            ][
                "lamports"
            ],

        "post_wsol_account_lamports":
            post_wsol[
                "lamports"
            ],

        "wsol_account_delta_lamports":
            post_wsol[
                "lamports"
            ]
            -pre[
                "wsol"
            ][
                "lamports"
            ],

        "pre_wsol_token_amount":
            pre[
                "wsol"
            ][
                "amount"
            ],

        "post_wsol_token_amount":
            post_wsol[
                "amount"
            ],

        "pre_token_amount":
            pre[
                "token"
            ][
                "amount"
            ],

        "post_token_amount":
            post_token[
                "amount"
            ],

        "residual_token_delta_raw":
            token_delta,

        "pre_wealth_lamports":
            pre_wealth,

        "post_wealth_lamports":
            post_wealth,

        "gross_wealth_delta_lamports":
            gross_delta,

        "estimated_fee_lamports":
            fee,

        "net_after_fee_lamports":
            net_after_fee,

        "logs":
            v.get("logs")
            or [],
    }


def executable_candidate(
    user,
    kp,
    route,
    candidate,
    alt_options,
    blockhash,
    token
):
    accounts,missing=(
        verify_account_lineage(
            user,
            token,
            candidate
        )
    )

    row={
        "name":
            candidate[
                "name"
            ],

        "pump_optional_removed":
            candidate[
                "pump_optional_removed"
            ],

        "account_lineage_missing":
            missing,
    }

    if missing:
        row.update({
            "compiled":False,
            "error":
                "EXECUTION_ACCOUNT_LINEAGE_MISSING:"
                +",".join(
                    missing
                ),
        })

        return row

    comp=q87.compile_candidate(
        user,
        candidate[
            "instructions"
        ],
        alt_options,
        blockhash
    )

    row.update({
        "compiled":
            bool(
                comp.get("ok")
            ),

        "compile_attempts":
            comp.get(
                "attempts",
                []
            ),
    })

    if not comp.get("ok"):
        row[
            "error"
        ]=comp.get(
            "error"
        )

        return row

    raw=c.signed_tx(
        comp[
            "msg"
        ],
        kp
    )

    row[
        "bytes"
    ]=len(raw)

    row[
        "alt_count"
    ]=len(
        comp[
            "alts"
        ]
    )

    if len(raw)>MAX_TX_BYTES:
        row[
            "error"
        ]="TX_TOO_LARGE_AFTER_SIGN"

        return row

    sim=simulate_wealth(
        raw,
        comp[
            "msg"
        ],
        user,
        token,
        accounts
    )

    gross=sim[
        "gross_wealth_delta_lamports"
    ]

    net=sim[
        "net_after_fee_lamports"
    ]

    gross_bps=(
        gross
        /route[
            "start_lamports"
        ]
        *10000.0
    )

    net_bps=(
        net
        /route[
            "start_lamports"
        ]
        *10000.0
        if net is not None
        else None
    )

    row.update({
        "sim_err":
            sim["err"],

        "sim_units":
            sim["units"],

        "gross_sim_pnl_lamports":
            gross,

        "gross_sim_bps":
            gross_bps,

        "estimated_fee_lamports":
            sim[
                "estimated_fee_lamports"
            ],

        "net_sim_pnl_lamports":
            net,

        "net_sim_bps":
            net_bps,

        "residual_token_delta_raw":
            sim[
                "residual_token_delta_raw"
            ],

        "native_delta_lamports":
            sim[
                "native_delta_lamports"
            ],

        "wsol_account_delta_lamports":
            sim[
                "wsol_account_delta_lamports"
            ],

        "pre_native_lamports":
            sim[
                "pre_native_lamports"
            ],

        "post_native_lamports":
            sim[
                "post_native_lamports"
            ],

        "pre_wsol_account_lamports":
            sim[
                "pre_wsol_account_lamports"
            ],

        "post_wsol_account_lamports":
            sim[
                "post_wsol_account_lamports"
            ],

        "profitable_after_fee":
            bool(
                sim["err"] is None
                and net is not None
                and net>0
                and net_bps
                    >=las.q59.MIN_NET_BPS
                and sim[
                    "residual_token_delta_raw"
                ]==0
            ),
    })

    return row


def run(root=None):
    root=Path(
        root or Path.cwd()
    )

    print(
        "[QARB-088] IN-PLACE "
        "EXECUTABLE PROFIT ACCOUNTING REPAIR",
        flush=True
    )

    print(
        "[ACCOUNTING] native SOL + "
        "WSOL account lamports; "
        "no WSOL double-count",
        flush=True
    )

    kp,user=c.sim_identity()

    try:
        signer=require_local_identity(
            kp,
            user
        )

    except RuntimeError as exc:
        out={
            "revision":
                "QARB_088_ACCOUNTING_REPAIR",

            "status":
                "HOLD",

            "reason":
                str(exc),

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
            root/STATE,
            out
        )

        print(
            "[IDENTITY_HOLD] %s"%(
                exc
            ),
            flush=True
        )

        print(
            "[MODE] simulation_only "
            "execution_authority=FALSE "
            "real_money_moved=FALSE",
            flush=True
        )

        return 2

    print(
        "[IDENTITY] local_signer=True "
        "pubkey=%s"%(
            signer
        ),
        flush=True
    )

    bindings,audit=(
        q87.q86.memory_candidates(
            root
        )
    )

    if not bindings:
        print(
            "[QARB-088 HOLD] "
            "no qualified bindings",
            flush=True
        )

        return 2

    pairs,_=q87.q86.hydrate(
        root,
        bindings
    )

    pair_map={
        p.token:p
        for p in pairs
    }

    try:
        extra_alts=(
            las.q59.recent_mriya_alt_keys()
        )
    except Exception:
        extra_alts=[]

    results={}

    compiled_tokens=set()
    simulated_tokens=set()
    measured_tokens=set()
    profitable_tokens=set()

    for binding in bindings:
        token=binding[
            "token"
        ]

        pair=pair_map.get(
            token
        )

        result={
            "token":token,

            "preferred_size_sol":
                binding[
                    "size_sol"
                ],

            "attempts":[],
        }

        results[
            token
        ]=result

        if pair is None:
            result[
                "status"
            ]="PAIR_MISSING"

            continue

        for size in q87.size_ladder(
            binding[
                "size_sol"
            ]
        ):
            try:
                route=q87.compose(
                    user,
                    pair,
                    size
                )

            except RuntimeError as exc:
                if str(exc)=="DLMM_PARTIAL":
                    continue

                result[
                    "status"
                ]=(
                    "COMPOSE_ERROR:"
                    +str(exc)
                )

                break

            if route[
                "pre_sim_net_lamports"
            ]<=0:
                continue

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

            legal_seen=False

            for candidate in q87.repaired_candidates(
                route
            ):
                row=executable_candidate(
                    user,
                    kp,
                    route,
                    candidate,
                    options,
                    bh,
                    token
                )

                row[
                    "size_sol"
                ]=size

                row[
                    "pre_sim_net_lamports"
                ]=route[
                    "pre_sim_net_lamports"
                ]

                row[
                    "pre_sim_bps"
                ]=route[
                    "pre_sim_bps"
                ]

                result[
                    "attempts"
                ].append(
                    row
                )

                if not row.get(
                    "compiled"
                ):
                    continue

                legal_seen=True

                compiled_tokens.add(
                    token
                )

                if "sim_err" not in row:
                    continue

                simulated_tokens.add(
                    token
                )

                if (
                    row.get(
                        "sim_err"
                    ) is None
                    and row.get(
                        "net_sim_pnl_lamports"
                    ) is not None
                ):
                    measured_tokens.add(
                        token
                    )

                if row.get(
                    "profitable_after_fee"
                ):
                    profitable_tokens.add(
                        token
                    )

                    result[
                        "winner"
                    ]=row

                    result[
                        "status"
                    ]="EXECUTABLE_2S_PROFIT_PASS"

                    break

            if result.get(
                "winner"
            ):
                break

            if legal_seen:
                result[
                    "status"
                ]="MEASURED_NO_EXECUTABLE_PROFIT"

                break

        if "status" not in result:
            result[
                "status"
            ]="NO_EXECUTABLE_SIZE"

    status=(
        "PASS"
        if measured_tokens
        else "HOLD"
    )

    out={
        "revision":
            "QARB_088_ACCOUNTING_REPAIR",

        "status":
            status,

        "signer":
            signer,

        "qualified_tokens":
            len(bindings),

        "compiled_tokens":
            len(
                compiled_tokens
            ),

        "simulated_tokens":
            len(
                simulated_tokens
            ),

        "measured_tokens":
            len(
                measured_tokens
            ),

        "profitable_tokens":
            len(
                profitable_tokens
            ),

        "results":
            results,

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
        root/STATE,
        out
    )

    for token,result in results.items():
        print(
            "[2S_EXEC_ECON] "
            "token=%s status=%s"%(
                token[:10],
                result[
                    "status"
                ]
            ),
            flush=True
        )

        for x in result[
            "attempts"
        ]:
            if not x.get(
                "compiled"
            ):
                continue

            print(
                "[2S_WEALTH_SIM] "
                "token=%s "
                "size=%.6f "
                "candidate=%s "
                "bytes=%s "
                "err=%s "
                "native_delta=%s "
                "wsol_delta=%s "
                "gross=%s "
                "fee=%s "
                "net=%s "
                "bps=%s "
                "residual_token=%s "
                "profitable=%s"%(
                    token[:10],

                    x[
                        "size_sol"
                    ],

                    x[
                        "name"
                    ],

                    x.get(
                        "bytes"
                    ),

                    x.get(
                        "sim_err"
                    ),

                    x.get(
                        "native_delta_lamports"
                    ),

                    x.get(
                        "wsol_account_delta_lamports"
                    ),

                    x.get(
                        "gross_sim_pnl_lamports"
                    ),

                    x.get(
                        "estimated_fee_lamports"
                    ),

                    x.get(
                        "net_sim_pnl_lamports"
                    ),

                    x.get(
                        "net_sim_bps"
                    ),

                    x.get(
                        "residual_token_delta_raw"
                    ),

                    x.get(
                        "profitable_after_fee"
                    ),
                ),
                flush=True
            )

        if result.get(
            "winner"
        ):
            w=result[
                "winner"
            ]

            print(
                "[2S_EXECUTABLE_PROFIT] "
                "token=%s "
                "size=%.6f "
                "net=%+.9f_SOL "
                "bps=%+.2f "
                "candidate=%s"%(
                    token[:10],

                    w[
                        "size_sol"
                    ],

                    w[
                        "net_sim_pnl_lamports"
                    ]/1e9,

                    w[
                        "net_sim_bps"
                    ],

                    w[
                        "name"
                    ],
                ),
                flush=True
            )

    print(
        "[QARB-088] status=%s "
        "compiled_tokens=%d "
        "simulated_tokens=%d "
        "measured_tokens=%d "
        "profitable_tokens=%d"%(
            status,

            len(
                compiled_tokens
            ),

            len(
                simulated_tokens
            ),

            len(
                measured_tokens
            ),

            len(
                profitable_tokens
            ),
        ),
        flush=True
    )

    print(
        "[MODE] simulation_only "
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
'''

tests=r'''import struct
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_088_two_second_executable_profit_accounting as q


class T(unittest.TestCase):

    def test_token_amount_decode(self):
        raw=bytearray(165)

        struct.pack_into(
            "<Q",
            raw,
            64,
            123456789
        )

        self.assertEqual(
            q.token_amount_from_data(
                bytes(raw)
            ),
            123456789
        )


    def test_short_token_rejected(self):
        with self.assertRaises(
            RuntimeError
        ):
            q.token_amount_from_data(
                b"\0"*20
            )


    def test_missing_account_zero(self):
        x=q.decode_rpc_account(
            None
        )

        self.assertFalse(
            x["exists"]
        )

        self.assertEqual(
            x["lamports"],
            0
        )


    def test_wsol_not_double_counted(self):
        # 3000 account lamports already include
        # the 2000 wrapped-SOL token amount.
        x=q.wealth_lamports(
            1000,
            {
                "amount":2000,
                "lamports":3000,
            }
        )

        self.assertEqual(
            x,
            4000
        )


    def test_fallback_identity_rejected(self):
        with self.assertRaises(
            RuntimeError
        ):
            q.require_local_identity(
                None,
                "fallback"
            )


    def test_exact_087_compose_reused(self):
        self.assertTrue(
            callable(
                q.q87.compose
            )
        )


    def test_exact_087_candidates_reused(self):
        self.assertTrue(
            callable(
                q.q87.repaired_candidates
            )
        )


    def test_exact_087_compile_reused(self):
        self.assertTrue(
            callable(
                q.q87.compile_candidate
            )
        )


    def test_max_tx_size(self):
        self.assertEqual(
            q.MAX_TX_BYTES,
            1232
        )


    def test_no_broadcast_boundary(self):
        src=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            'c.send(',
            src
        )


    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
'''

launcher=r'''from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering.qarb_088_two_second_executable_profit_accounting import main

if __name__=="__main__":
    raise SystemExit(main())
'''

M.write_text(
    module,
    encoding="utf-8"
)

T.write_text(
    tests,
    encoding="utf-8"
)

U.write_text(
    launcher,
    encoding="utf-8"
)

for p in (M,T,U):
    py_compile.compile(
        str(p),
        doraise=True
    )

print(
    "[PASS] QARB-088 in-place executable-profit accounting repair installed"
)
print(
    "[FIX] WSOL principal no longer double-counted"
)
print(
    "[FIX] fallback/Mriya simulation identity rejected"
)
print(
    "[LINEAGE] payer + WSOL ATA + token ATA must exist in exact candidate"
)
print(
    "[INPUT] certified QARB-087 transaction path unchanged"
)
print(
    "[MODE] simulation_only execution_authority=FALSE real_money_moved=FALSE"
)