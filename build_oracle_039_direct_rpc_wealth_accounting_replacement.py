from pathlib import Path
import ast

ROOT=Path.cwd()
SUB=ROOT/"qseries_v2"/"oracle_execution"
SUB.mkdir(parents=True,exist_ok=True)

MOD=SUB/"oracle_039_direct_rpc_wealth_accounting_replacement.py"
TEST=ROOT/"test_oracle_039_direct_rpc_wealth_accounting_replacement.py"
RUN=ROOT/"run_oracle_039_direct_rpc_wealth_accounting_replacement.py"

MODULE_SOURCE=r'''
from __future__ import annotations

import base64
from collections.abc import Mapping

from qseries_v2.oracle_execution import (
    oracle_038_candidate_compile_isolation_compact_recovery as q38
)

c=q38.q87.c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False


def rpc_direct(method,params):
    j=c.http(
        c.RPC,
        "POST",
        {
            "jsonrpc":"2.0",
            "id":1,
            "method":method,
            "params":params,
        },
        15,
    )

    if not isinstance(j,Mapping):
        raise RuntimeError(
            "DIRECT_RPC_ENVELOPE_NOT_MAPPING:"
            +type(j).__name__
        )

    if j.get("error"):
        raise RuntimeError(
            "DIRECT_RPC_%s:%s"
            %(method,j["error"])
        )

    return j.get("result")


def account_info(addr):
    x=rpc_direct(
        "getAccountInfo",
        [
            addr,
            {
                "encoding":"base64",
                "commitment":"processed",
            },
        ],
    )

    if not isinstance(x,Mapping):
        raise RuntimeError(
            "ACCOUNT_RESULT_NOT_MAPPING:"
            +type(x).__name__
        )

    row=x.get("value")

    if row is None:
        return {
            "exists":False,
            "lamports":0,
            "amount":0,
            "owner":None,
        }

    if not isinstance(row,Mapping):
        raise RuntimeError(
            "ACCOUNT_VALUE_NOT_MAPPING:"
            +type(row).__name__
        )

    data=row.get("data")
    raw=None

    if isinstance(data,list) and data:
        raw=base64.b64decode(data[0])

    amount=0

    if raw is not None:
        amount=q38.q88.token_amount_from_data(raw)

    return {
        "exists":True,
        "lamports":int(row.get("lamports") or 0),
        "amount":int(amount),
        "owner":row.get("owner"),
    }


def mint_program(mint):
    x=rpc_direct(
        "getAccountInfo",
        [
            mint,
            {
                "encoding":"base64",
                "commitment":"processed",
            },
        ],
    )

    if not isinstance(x,Mapping):
        raise RuntimeError(
            "MINT_RESULT_NOT_MAPPING:"
            +type(x).__name__
        )

    row=x.get("value")

    if not isinstance(row,Mapping):
        raise RuntimeError(
            "MINT_ACCOUNT_MISSING:"+str(mint)
        )

    owner=row.get("owner")

    if not owner:
        raise RuntimeError(
            "MINT_OWNER_MISSING:"+str(mint)
        )

    return str(owner)


def native_balance(user):
    x=rpc_direct(
        "getBalance",
        [
            user,
            {"commitment":"processed"},
        ],
    )

    if not isinstance(x,Mapping):
        raise RuntimeError(
            "BALANCE_RESULT_NOT_MAPPING:"
            +type(x).__name__
        )

    return int(x.get("value") or 0)


def derive_accounts(user,token):
    wsol_program=mint_program(c.WSOL)
    token_program=mint_program(token)

    return {
        "wsol_ata":c.ata(
            user,
            c.WSOL,
            wsol_program,
        ),
        "token_ata":c.ata(
            user,
            token,
            token_program,
        ),
    }


def fee_for_message(message):
    x=rpc_direct(
        "getFeeForMessage",
        [
            base64.b64encode(message).decode(),
            {"commitment":"processed"},
        ],
    )

    if not isinstance(x,Mapping):
        raise RuntimeError(
            "FEE_RESULT_NOT_MAPPING:"
            +type(x).__name__
        )

    value=x.get("value")

    return (
        None
        if value is None
        else int(value)
    )


def simulation_value(raw,addresses,sigverify=False):
    x=rpc_direct(
        "simulateTransaction",
        [
            base64.b64encode(raw).decode(),
            {
                "encoding":"base64",
                "sigVerify":bool(sigverify),
                "commitment":"processed",
                "accounts":{
                    "encoding":"base64",
                    "addresses":addresses,
                },
            },
        ],
    )

    if not isinstance(x,Mapping):
        raise RuntimeError(
            "SIM_RESULT_NOT_MAPPING:"
            +type(x).__name__
        )

    v=x.get("value")

    if not isinstance(v,Mapping):
        raise RuntimeError(
            "SIM_VALUE_NOT_MAPPING:"
            +type(v).__name__
        )

    return v


def simulated_account(row):
    if row is None:
        return {
            "exists":False,
            "lamports":0,
            "amount":0,
            "owner":None,
        }

    if not isinstance(row,Mapping):
        raise RuntimeError(
            "SIM_ACCOUNT_NOT_MAPPING:"
            +type(row).__name__
        )

    data=row.get("data")
    raw=None

    if isinstance(data,list) and data:
        raw=base64.b64decode(data[0])

    amount=0

    if raw is not None:
        amount=q38.q88.token_amount_from_data(raw)

    return {
        "exists":True,
        "lamports":int(row.get("lamports") or 0),
        "amount":int(amount),
        "owner":row.get("owner"),
    }


def wealth(native,wsol):
    return (
        int(native)
        +int(wsol["amount"])
        +int(wsol["lamports"])
    )


def simulate_wealth(
    raw,
    message,
    user,
    token,
    sigverify=False,
):
    accounts=derive_accounts(
        user,
        token,
    )

    pre_native=native_balance(user)
    pre_wsol=account_info(
        accounts["wsol_ata"]
    )
    pre_token=account_info(
        accounts["token_ata"]
    )

    addresses=[
        user,
        accounts["wsol_ata"],
        accounts["token_ata"],
    ]

    v=simulation_value(
        raw,
        addresses,
        sigverify=False,
    )

    returned=list(
        v.get("accounts") or []
    )

    while len(returned)<3:
        returned.append(None)

    native_row=returned[0]

    post_native=(
        int(native_row.get("lamports") or 0)
        if isinstance(native_row,Mapping)
        else pre_native
    )

    post_wsol=simulated_account(
        returned[1]
    )

    post_token=simulated_account(
        returned[2]
    )

    pre_wealth=wealth(
        pre_native,
        pre_wsol,
    )

    post_wealth=wealth(
        post_native,
        post_wsol,
    )

    gross=post_wealth-pre_wealth

    fee=fee_for_message(message)

    net=(
        gross-fee
        if fee is not None
        else None
    )

    residual=(
        post_token["amount"]
        -pre_token["amount"]
    )

    return {
        "err":v.get("err"),
        "units":v.get("unitsConsumed"),

        "pre_native_lamports":
            pre_native,

        "post_native_lamports":
            post_native,

        "pre_wsol_amount":
            pre_wsol["amount"],

        "post_wsol_amount":
            post_wsol["amount"],

        "pre_wsol_rent_lamports":
            pre_wsol["lamports"],

        "post_wsol_rent_lamports":
            post_wsol["lamports"],

        "pre_token_amount":
            pre_token["amount"],

        "post_token_amount":
            post_token["amount"],

        "residual_token_delta_raw":
            residual,

        "gross_wealth_delta_lamports":
            gross,

        "estimated_fee_lamports":
            fee,

        "net_after_fee_lamports":
            net,

        "logs":
            v.get("logs") or [],
    }


def install():
    # Retire failed QARB-088 RPC/account assumptions
    # from the active ORACLE arbitration lane.
    q38.q88.simulate_wealth=simulate_wealth
    return True


def run(seconds=300.0):
    install()

    print(
        "[ORACLE-039] DIRECT RPC WEALTH ACCOUNTING REPLACEMENT",
        flush=True,
    )
    print(
        "[RETIRED] QARB-088 patched/shared RPC response assumptions",
        flush=True,
    )
    print(
        "[RPC] direct JSON-RPC result/value contracts",
        flush=True,
    )
    print(
        "[SIM] nested simulateTransaction result.value decoded",
        flush=True,
    )
    print(
        "[ACCOUNTING] native + WSOL amount + WSOL rent - fee",
        flush=True,
    )
    print(
        "[RESIDUAL] intermediate token delta required",
        flush=True,
    )
    print(
        "[BROADCAST] disabled",
        flush=True,
    )

    return q38.run(seconds=seconds)
'''

TEST_SOURCE=r'''
import unittest
from unittest.mock import patch

from qseries_v2.oracle_execution import (
    oracle_039_direct_rpc_wealth_accounting_replacement as q39
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(
            q39.EXECUTION_AUTHORITY
        )
        self.assertTrue(
            q39.PAPER_ONLY
        )
        self.assertFalse(
            q39.REAL_MONEY_MOVED
        )

    def test_direct_rpc_result(self):
        with patch.object(
            q39.c,
            "http",
            return_value={
                "jsonrpc":"2.0",
                "id":1,
                "result":{"value":123},
            },
        ):
            x=q39.rpc_direct(
                "getBalance",
                [],
            )

        self.assertEqual(
            x["value"],
            123,
        )

    def test_sim_nested_value(self):
        with patch.object(
            q39,
            "rpc_direct",
            return_value={
                "context":{"slot":1},
                "value":{
                    "err":None,
                    "accounts":[
                        {"lamports":100},
                        None,
                        None,
                    ],
                    "unitsConsumed":77,
                },
            },
        ):
            v=q39.simulation_value(
                b"x",
                ["U","W","T"],
                False,
            )

        self.assertIsNone(
            v["err"]
        )
        self.assertEqual(
            v["unitsConsumed"],
            77,
        )

    def test_bool_result_rejected_cleanly(self):
        with patch.object(
            q39,
            "rpc_direct",
            return_value=True,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "BALANCE_RESULT_NOT_MAPPING",
            ):
                q39.native_balance("U")

    def test_install_replaces_q88_wealth(self):
        q39.install()

        self.assertIs(
            q39.q38.q88.simulate_wealth,
            q39.simulate_wealth,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
'''

RUN_SOURCE=r'''
import argparse

from qseries_v2.oracle_execution.oracle_039_direct_rpc_wealth_accounting_replacement import run

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument(
        "--seconds",
        type=float,
        default=300.0,
    )
    a=p.parse_args()

    raise SystemExit(
        run(seconds=a.seconds)
    )
'''

ast.parse(MODULE_SOURCE)
ast.parse(TEST_SOURCE)
ast.parse(RUN_SOURCE)

MOD.write_text(
    MODULE_SOURCE.lstrip(),
    encoding="utf-8",
)

TEST.write_text(
    TEST_SOURCE.lstrip(),
    encoding="utf-8",
)

RUN.write_text(
    RUN_SOURCE.lstrip(),
    encoding="utf-8",
)

print("[PASS] ORACLE-039 direct RPC wealth accounting replacement installed")
print("[RETIRED] failed QARB-088 shared-RPC wealth boundary from active lane")
print("[FIX] simulateTransaction result.value decoded explicitly")
print("[FIX] all RPC mapping contracts type-checked")
print("[BROADCAST] disabled")